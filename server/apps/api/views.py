# -*- coding: utf-8 -*-

from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from server.apps.api.logic.mixins import ClientIPMixin
from server.apps.api.logic.serializers import (
    CaseSerializer,
    ConfigSerializer,
    DomainListSerializer,
)
from server.apps.api.logic.throttling import CreateCaseRateThrottle
from server.apps.api.models import Domain
from server.apps.core.models import Config, Country


class CaseCreateAPIView(ClientIPMixin, generics.CreateAPIView):
    serializer_class = CaseSerializer
    permission_classes = [AllowAny]
    throttle_classes = [CreateCaseRateThrottle]

    def create(self, request, *args, **kwargs):
        domain = request.data.get("domain")
        hostname = request.data.get("hostname")

        if not domain:
            domain = hostname

        if not domain:
            return Response(
                {"error": "Domain required"}, status=status.HTTP_400_BAD_REQUEST
            )

        domain_obj, _ = Domain.objects.get_or_create(domain=domain)
        request.data["domain"] = domain_obj.pk
        request.data["client_ip"] = self.get_client_ip()

        try:
            request.data["client_country"] = Country.objects.get(
                iso_a2_code=self.get_client_country_code()
            ).pk
        except Country.DoesNotExist:
            pass

        serializer = self.serializer_class(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({"status": status.HTTP_201_CREATED, "message": "created"})
        except ValidationError:
            return Response(
                {"errors": (serializer.errors,)}, status=status.HTTP_400_BAD_REQUEST
            )


class DomainListView(generics.ListAPIView):
    serializer_class = DomainListSerializer
    permission_classes = [AllowAny]
    queryset = Domain.objects.all()


class ConfigRetrieveAPIView(ClientIPMixin, generics.RetrieveAPIView):
    serializer_class = ConfigSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        client_country_code = self.get_client_country_code()
        return get_object_or_404(Config, country__iso_a2_code=client_country_code)
