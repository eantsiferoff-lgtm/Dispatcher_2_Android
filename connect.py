import os, sys
from dotenv import load_dotenv
from core.composio_gateway import ComposioGateway

load_dotenv()
toolkit = sys.argv[1] if len(sys.argv) > 1 else 'gmail'
gw = ComposioGateway()
info = gw.authorize(toolkit)
print(f'Connect {toolkit} in your browser:')
print(info['redirect_url'])
print(f'After OAuth, the connection is stored for DISPATCHER_USER_ID={gw.user_id}.')
