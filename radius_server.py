#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zinar RADIUS Server (ملف واحد مكتفٍ ذاتياً)
----------------------------------------
سيرفر RADIUS مركزي يصادق مشتركي منصة زينار مباشرة من نفس قاعدة البيانات.
كل شيء في ملف واحد: قاموس RADIUS مدمج داخل الملف (لا حاجة لملف dictionary منفصل).

- يستمع على UDP 1812 (مصادقة) و 1813 (محاسبة/استهلاك).
- لا يُضاف أي حساب داخل الراوتر: كل الحسابات تبقى مركزية في قاعدة البيانات.
- يدعم PAP و CHAP (وهو الافتراضي في هوتسبوت مايكروتيك).
- يعيد حد السرعة (Mikrotik-Rate-Limit) حسب باقة المشترك.

التشغيل:  python3 radius_server.py
المتغيرات البيئية:
  DATABASE_URL   نفس رابط قاعدة بيانات المنصة (PostgreSQL أو sqlite محلي)
  RADIUS_SECRET  الكلمة السرية المشتركة (مثال: zinar123)
  RADIUS_AUTH_PORT  افتراضي 1812
  RADIUS_ACCT_PORT  افتراضي 1813

ملاحظة: لا يعمل على Render (يدعم HTTPS فقط). ضعه على VPS بـIP عام،
ووجّه المايكروتيك إلى عنوان الـVPS.
المتطلبات:  pip install pyrad sqlalchemy
"""

import os
import datetime
import tempfile
import traceback

from pyrad.server import Server, RemoteHost
from pyrad.dictionary import Dictionary
from pyrad import packet

from sqlalchemy import create_engine, text

# ---------------- قاموس RADIUS مدمج داخل الملف ----------------
DICTIONARY_DATA = """
ATTRIBUTE\tUser-Name\t\t1\tstring
ATTRIBUTE\tUser-Password\t\t2\tstring
ATTRIBUTE\tCHAP-Password\t\t3\toctets
ATTRIBUTE\tNAS-IP-Address\t\t4\tipaddr
ATTRIBUTE\tNAS-Port\t\t5\tinteger
ATTRIBUTE\tService-Type\t\t6\tinteger
ATTRIBUTE\tFramed-Protocol\t\t7\tinteger
ATTRIBUTE\tFramed-IP-Address\t8\tipaddr
ATTRIBUTE\tFramed-IP-Netmask\t9\tipaddr
ATTRIBUTE\tFilter-Id\t\t11\tstring
ATTRIBUTE\tFramed-MTU\t\t12\tinteger
ATTRIBUTE\tReply-Message\t\t18\tstring
ATTRIBUTE\tState\t\t\t24\toctets
ATTRIBUTE\tClass\t\t\t25\toctets
ATTRIBUTE\tVendor-Specific\t\t26\toctets
ATTRIBUTE\tSession-Timeout\t\t27\tinteger
ATTRIBUTE\tIdle-Timeout\t\t28\tinteger
ATTRIBUTE\tCalled-Station-Id\t30\tstring
ATTRIBUTE\tCalling-Station-Id\t31\tstring
ATTRIBUTE\tNAS-Identifier\t\t32\tstring
ATTRIBUTE\tAcct-Status-Type\t40\tinteger
ATTRIBUTE\tAcct-Delay-Time\t\t41\tinteger
ATTRIBUTE\tAcct-Input-Octets\t42\tinteger
ATTRIBUTE\tAcct-Output-Octets\t43\tinteger
ATTRIBUTE\tAcct-Session-Id\t\t44\tstring
ATTRIBUTE\tAcct-Authentic\t\t45\tinteger
ATTRIBUTE\tAcct-Session-Time\t46\tinteger
ATTRIBUTE\tAcct-Input-Packets\t47\tinteger
ATTRIBUTE\tAcct-Output-Packets\t48\tinteger
ATTRIBUTE\tAcct-Terminate-Cause\t49\tinteger
ATTRIBUTE\tAcct-Input-Gigawords\t52\tinteger
ATTRIBUTE\tAcct-Output-Gigawords\t53\tinteger
ATTRIBUTE\tCHAP-Challenge\t\t60\toctets
ATTRIBUTE\tNAS-Port-Type\t\t61\tinteger
ATTRIBUTE\tPort-Limit\t\t62\tinteger
ATTRIBUTE\tMessage-Authenticator\t80\toctets

VALUE\tAcct-Status-Type\tStart\t\t1
VALUE\tAcct-Status-Type\tStop\t\t2
VALUE\tAcct-Status-Type\tInterim-Update\t3

VALUE\tService-Type\tLogin-User\t\t1
VALUE\tService-Type\tFramed-User\t\t2

VENDOR\t\tMikrotik\t14988
BEGIN-VENDOR\tMikrotik
ATTRIBUTE\tMikrotik-Recv-Limit\t\t1\tinteger
ATTRIBUTE\tMikrotik-Xmit-Limit\t\t2\tinteger
ATTRIBUTE\tMikrotik-Group\t\t\t3\tstring
ATTRIBUTE\tMikrotik-Wireless-Forward\t4\tinteger
ATTRIBUTE\tMikrotik-Wireless-Skip-Dot1x\t5\tinteger
ATTRIBUTE\tMikrotik-Rate-Limit\t\t8\tstring
ATTRIBUTE\tMikrotik-Realm\t\t\t9\tstring
ATTRIBUTE\tMikrotik-Host-IP\t\t10\tipaddr
ATTRIBUTE\tMikrotik-Mark-Id\t\t11\tstring
ATTRIBUTE\tMikrotik-Advertise-URL\t\t12\tstring
ATTRIBUTE\tMikrotik-Advertise-Interval\t13\tinteger
ATTRIBUTE\tMikrotik-Recv-Limit-Gigawords\t14\tinteger
ATTRIBUTE\tMikrotik-Xmit-Limit-Gigawords\t15\tinteger
ATTRIBUTE\tMikrotik-Wireless-Enc-Algo\t16\tinteger
ATTRIBUTE\tMikrotik-Wireless-Enc-Key\t17\tstring
ATTRIBUTE\tMikrotik-Rate-Limit-Rx\t\t18\tstring
ATTRIBUTE\tMikrotik-Rate-Limit-Tx\t\t19\tstring
ATTRIBUTE\tMikrotik-Total-Limit\t\t20\tinteger
ATTRIBUTE\tMikrotik-Address-List\t\t21\tstring
END-VENDOR\tMikrotik
"""


def _load_dictionary():
    """يكتب القاموس المدمج إلى ملف مؤقت ثم يحمّله (حتى يبقى كل شيء في ملف واحد)."""
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.dict',
                                      delete=False, encoding='utf-8')
    tmp.write(DICTIONARY_DATA)
    tmp.close()
    return Dictionary(tmp.name)


# ---------------- إعداد قاعدة البيانات ----------------
DB_URL = os.environ.get('DATABASE_URL', 'sqlite:///zinar_radius.db')
if DB_URL.startswith('postgres://'):
    DB_URL = DB_URL.replace('postgres://', 'postgresql://', 1)

engine = create_engine(DB_URL, pool_pre_ping=True, pool_recycle=1800)

SECRET = os.environ.get('RADIUS_SECRET', 'zinar123').encode()
AUTH_PORT = int(os.environ.get('RADIUS_AUTH_PORT', 1812))
ACCT_PORT = int(os.environ.get('RADIUS_ACCT_PORT', 1813))


# ---------------- دوال قاعدة البيانات ----------------
def get_user(username):
    """يجلب المشترك من جدول radius_user."""
    sql = text("""
        SELECT username, password, status, plan_name, expire_date, allowed_data
        FROM radius_user WHERE username = :u LIMIT 1
    """)
    with engine.connect() as conn:
        row = conn.execute(sql, {'u': username}).mappings().first()
    return dict(row) if row else None


def get_package_speed(plan_name):
    """يعيد (download_speed, upload_speed) للباقة، أو قيم افتراضية."""
    if not plan_name:
        return ('5M', '1M')
    sql = text("""
        SELECT download_speed, upload_speed FROM package
        WHERE name = :n LIMIT 1
    """)
    try:
        with engine.connect() as conn:
            row = conn.execute(sql, {'n': plan_name}).mappings().first()
        if row:
            return (row['download_speed'] or '5M', row['upload_speed'] or '1M')
    except Exception:
        pass
    return ('5M', '1M')


def is_expired(expire_date):
    """expire_date مخزّن كنص بصيغة dd-mm-YYYY."""
    if not expire_date:
        return False
    for fmt in ('%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y'):
        try:
            d = datetime.datetime.strptime(str(expire_date), fmt).date()
            return d < datetime.date.today()
        except ValueError:
            continue
    return False


def update_usage(username, in_octets, out_octets, session_time):
    """تحديث الاستهلاك عند وصول رسائل المحاسبة (Accounting)."""
    dl_gb = round((out_octets or 0) / (1024 ** 3), 2)
    ul_gb = round((in_octets or 0) / (1024 ** 3), 2)
    sql = text("""
        UPDATE radius_user
        SET download_gb = :dl, upload_gb = :ul,
            used_data_gb = :used, uptime = :up
        WHERE username = :u
    """)
    try:
        with engine.begin() as conn:
            conn.execute(sql, {
                'dl': dl_gb, 'ul': ul_gb,
                'used': round(dl_gb + ul_gb, 2),
                'up': f'{int(session_time or 0)}s',
                'u': username,
            })
    except Exception as e:
        print('[ACCT] فشل تحديث الاستهلاك:', e)


# ---------------- سيرفر RADIUS ----------------
class ZinarRadiusServer(Server):

    def _verify_password(self, pkt, stored_password):
        """يتحقق من كلمة المرور سواء PAP أو CHAP."""
        if 'User-Password' in pkt:
            try:
                given = pkt.PwDecrypt(pkt['User-Password'][0])
                return given == stored_password
            except Exception:
                return False
        if 'CHAP-Password' in pkt:
            try:
                return pkt.VerifyChapPasswd(stored_password)
            except Exception:
                return False
        return False

    def HandleAuthPacket(self, pkt):
        username = pkt['User-Name'][0] if 'User-Name' in pkt else ''
        reply = self.CreateReplyPacket(pkt)
        print(f'[AUTH] طلب مصادقة للمستخدم: {username}')

        user = get_user(username)
        accept = False
        reason = ''

        if not user:
            reason = 'المستخدم غير موجود'
        elif str(user['status']).strip() not in ('مفعل', 'active', 'enabled', 'مُفعّل'):
            reason = 'الحساب غير مفعّل'
        elif is_expired(user['expire_date']):
            reason = 'انتهى الاشتراك'
        elif not self._verify_password(pkt, user['password']):
            reason = 'كلمة المرور غير صحيحة'
        else:
            accept = True

        if accept:
            dl, ul = get_package_speed(user['plan_name'])
            rate_limit = f'{ul}/{dl}'
            reply['Mikrotik-Rate-Limit'] = rate_limit
            reply.code = packet.AccessAccept
            print(f'[AUTH] قبول {username} | سرعة {rate_limit}')
        else:
            reply['Reply-Message'] = reason[:200]
            reply.code = packet.AccessReject
            print(f'[AUTH] رفض {username} | السبب: {reason}')

        self.SendReplyPacket(pkt.fd, reply)

    def HandleAcctPacket(self, pkt):
        username = pkt['User-Name'][0] if 'User-Name' in pkt else ''
        status = pkt['Acct-Status-Type'][0] if 'Acct-Status-Type' in pkt else ''

        def _num(attr):
            return pkt[attr][0] if attr in pkt else 0

        in_oct = _num('Acct-Input-Octets')
        out_oct = _num('Acct-Output-Octets')
        sess_time = _num('Acct-Session-Time')

        if username and status in ('Stop', 'Interim-Update', 2, 3):
            update_usage(username, in_oct, out_oct, sess_time)
            print(f'[ACCT] {username} | {status} | تنزيل={out_oct}B رفع={in_oct}B')

        reply = self.CreateReplyPacket(pkt)
        self.SendReplyPacket(pkt.fd, reply)


class AnyHosts(dict):
    """يسمح لأي راوتر بالاتصال ما دام يستخدم نفس الكلمة السرية."""
    def __init__(self, secret):
        super().__init__()
        self._secret = secret

    def __contains__(self, key):
        return True

    def __getitem__(self, key):
        return RemoteHost(key, self._secret, str(key))


def main():
    srv = ZinarRadiusServer(
        dict=_load_dictionary(),
        authport=AUTH_PORT,
        acctport=ACCT_PORT,
        coaport=3799,
    )
    srv.hosts = AnyHosts(SECRET)
    srv.BindToAddress('0.0.0.0')

    print('=' * 55)
    print('  Zinar RADIUS Server يعمل الآن')
    print(f'  مصادقة UDP: {AUTH_PORT} | محاسبة UDP: {ACCT_PORT}')
    print(f'  قاعدة البيانات: {DB_URL.split("@")[-1]}')
    print('=' * 55)

    try:
        srv.Run()
    except KeyboardInterrupt:
        print('\nتم الإيقاف.')
    except Exception:
        traceback.print_exc()


if __name__ == '__main__':
    main()


