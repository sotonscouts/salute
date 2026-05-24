import strawberry as sb
import strawberry_django as sd

from salute.api.extensions import IsServiceAccountWithScope
from salute.api.scopes import ApiScope
from salute.wifi.graphql.graph_types import WifiAccount


@sb.type
class WifiQuery:
    wifi_accounts: sd.relay.DjangoListConnection[WifiAccount] = sd.connection(
        description="List WiFi accounts",
        extensions=[IsServiceAccountWithScope(ApiScope.WIFI_ACCOUNTS_READ, fail_silently=False)],
    )
