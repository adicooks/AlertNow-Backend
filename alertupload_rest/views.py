from alertupload_rest.serializers import UploadAlertSerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.http import JsonResponse
from threading import Thread
from django.core.mail import send_mail
import re
from twilio.rest import Client
from django.conf import settings

def start_new_thread(function):
    def decorator(*args, **kwargs):
        t = Thread(target = function, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()
    return decorator

@api_view(['POST'])
def post_alert(request):
    serializer = UploadAlertSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        identify_email_sms(serializer)

    else:
        return JsonResponse({'error': 'Unable to process data!'}, status=400)

    return Response(request.META.get('HTTP_AUTHORIZATION'))

def identify_email_sms(serializer):
    if(re.search('^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$', serializer.data['alert_receiver'])):
        print("Valid Email")
        send_email(serializer)
    elif re.compile("[0-9]{9}").match(serializer.data['alert_receiver']):
        print("Valid Mobile Number")
        send_sms(serializer)
    else:
        print("Invalid Email or Mobile number")

@start_new_thread
def send_email(serializer):
    send_mail('Weapon Detected!',
    prepare_alert_message(serializer),
    'blazenotify2021@gmail.com',
    [serializer.data['alert_receiver']],
    fail_silently=False,)

# Sends SMS
@start_new_thread
def send_sms(serializer):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    message = client.messages.create(body=prepare_alert_message(serializer),
                                    from_=settings.TWILIO_NUMBER,
                                    to=serializer.data['alert_receiver'])

def prepare_alert_message(serializer):
    image_path = serializer.data['image']
    path_parts = split(image_path, "/")

    if len(path_parts) > 1:
        uuid_with_extension = path_parts[-1]

        uuid_parts = split(uuid_with_extension, ".")

        if len(uuid_parts) > 1:
            uuid = uuid_parts[0]
            url = 'http://127.0.0.1:8000/alert/' + uuid
            return 'Weapon Detected! View alert at ' + url
        else:
            return 'Invalid image format: UUID and extension missing'
    else:
        return 'Invalid image format: Path incorrect'

# Splits string into a list
def split(value, key):
    return str(value).split(key)


