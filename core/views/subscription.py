from rest_framework.generics import (
    ListAPIView,
    RetrieveUpdateDestroyAPIView,
)


from core.permissions import IsSuperAdminOrReadOnly
from core.models import Subscription
from core.serializers.subscription import (
    SubscriptionListSerializer,
    SubscriptionDetailSerializer,
)


class SubscriptionList(ListAPIView):
    queryset = Subscription().get_all_actives()
    serializer_class = SubscriptionListSerializer
    # pagination_class = None  # Disable pagination if not needed
    permission_classes = [IsSuperAdminOrReadOnly]


class SubscriptionDetail(RetrieveUpdateDestroyAPIView):
    queryset = Subscription().get_all_actives()
    serializer_class = SubscriptionDetailSerializer
    lookup_field = "uid"
    permission_classes = [IsSuperAdminOrReadOnly]
