import json
import requests
import urllib.parse
from amsterdam_app_api.GenericFunctions.StaticData import StaticData
from amsterdam_app_api.GenericFunctions.Distance import Distance
from amsterdam_app_api.GenericFunctions.Sort import Sort
from amsterdam_app_api.api_messages import Messages
from amsterdam_app_api.models import ProjectDetails, Projects
from amsterdam_app_api.serializers import ProjectsSerializer
from amsterdam_app_api.swagger.swagger_views_distance import as_distance
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema

messages = Messages()


@swagger_auto_schema(**as_distance)
@api_view(['GET'])
def distance(request):
    """ Get distance 'in bird flight' from user to projects
    """
    def get_projects_data(_identifier, _model_items, _distance):
        projects_object = Projects.objects.filter(pk=_identifier).first()

        if _model_items is not None:
            fields = _model_items.split(',')
            serializer = ProjectsSerializer(projects_object, context={'fields': fields}, many=False)
        else:
            serializer = ProjectsSerializer(projects_object, many=False)

        result = serializer.data
        result['meter'] = int(distance.meter)
        result['strides'] = int(distance.strides)
        return result

    lat = request.GET.get('lat', None)
    lon = request.GET.get('lon', None)
    radius = request.GET.get('radius', None)
    address = request.GET.get('address', None)  # akkerstraat%2014 -> akkerstraat 14
    model_items = request.GET.get('fields', None)

    if address is not None:
        apis = StaticData.urls()
        url = '{api}{address}'.format(api=apis['address_to_gps'], address=urllib.parse.quote_plus(address))
        result = requests.get(url=url, timeout=1)
        data = json.loads(result.content)
        if len(data['results']) == 1:
            lon = data['results'][0]['centroid'][0]
            lat = data['results'][0]['centroid'][1]

    if lat is None or lon is None:
        return Response({'status': False, 'result': messages.distance_params}, 422)

    try:
        cords_1 = (float(lat), float(lon))
    except Exception as error:
        return Response({'status': False, 'result': str(error)}, 500)

    results = list()
    projects = list(ProjectDetails.objects.filter().all())
    for project in projects:
        cords_2 = (project.coordinates['lat'], project.coordinates['lon'])
        distance = Distance(cords_1, cords_2)

        if radius is None:
            result = get_projects_data(project.identifier, model_items, distance)
            results.append(result)
        elif distance.meter < float(radius):
            result = get_projects_data(project.identifier, model_items, distance)
            results.append(result)

    sorted_results = Sort().list_of_dicts(results, key='meter', sort_order='asc')
    return Response({'status': True, 'result': sorted_results})
