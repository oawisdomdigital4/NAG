from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from community.models import CorporateOpportunity, CorporateConnection
from .serializers import OpportunityListSerializer, ConnectionListSerializer
from django.db.models import Q, Count

class OpportunityViewSet(viewsets.ModelViewSet):
    serializer_class = OpportunityListSerializer
    
    def get_permissions(self):
        """Allow unauthenticated access for list/retrieve, require auth for mutations"""
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        # All users see all open opportunities
        # Corporate users managing their own can use CorporateOpportunityViewSet in community app
        return CorporateOpportunity.objects.filter(status='open').order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

class ConnectionViewSet(viewsets.ModelViewSet):
    serializer_class = ConnectionListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return CorporateConnection.objects.filter(
            Q(sender=user) | Q(receiver=user)
        ).select_related('sender', 'receiver')
    
    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

class CorporateConnectionStats(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        connections = CorporateConnection.objects.filter(
            Q(sender=user) | Q(receiver=user)
        )
        
        stats = {
            'total_connections': connections.filter(status='accepted').count(),
            'pending_requests': connections.filter(status='pending').count(),
            'recent_activity': [],  # Would be populated from your activity tracking system
            'industry_breakdown': {}  # Would be calculated from connected partners' industries
        }
        
        return Response(stats)

class OpportunityStats(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        # Get all open opportunities statistics
        opportunities = CorporateOpportunity.objects.filter(status='open')
        
        stats = {
            'total': opportunities.count(),
            'open': opportunities.filter(status='open').count(),
            'closingSoon': opportunities.filter(closing_soon=True).count() if hasattr(CorporateOpportunity, 'closing_soon') else 0,
            'applications': sum([opp.application_count for opp in opportunities]) if hasattr(CorporateOpportunity, 'application_count') else 0,
            'by_type': list(opportunities.values('opportunity_type').annotate(count=Count('id'))),
            'by_location': list(opportunities.values('location').annotate(count=Count('id'))),
        }
        
        return Response(stats)