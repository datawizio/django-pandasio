import pandas as pd

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status


class BaseModelDataFrameView(viewsets.ModelViewSet):

    def create(self, request, *args, **kwargs):
        dataframe = self.get_dataframe_from_request(request=request)
        serializer = self.get_serializer(data=dataframe)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response(status=status.HTTP_201_CREATED)

    def get_dataframe_from_request(self, request):
        raise NotImplementedError


class RecordsModelDataFrameView(BaseModelDataFrameView):

    def get_dataframe_from_request(self, request):
        return pd.DataFrame.from_records(request.data)
