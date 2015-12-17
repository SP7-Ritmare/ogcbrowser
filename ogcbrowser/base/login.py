from django.contrib.auth import authenticate, login
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils import simplejson

def ajax_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        if username and password:
            # Test username/password combination
            user = authenticate(username=username, password=password)
            # Found a match
            if user is not None:
                # User is active
                if user.is_active:
                    # Officially log the user in
                    login(self.request, user)
                    data = {'success': True}
                else:
                    data = {'success': False, 'error': 'User is not active'}
            else:
                data = {'success': False, 'error': 'Wrong username and/or password'}
            return HttpResponse(simplejson.dumps(data), mimetype='application/json')

    # Request method is not POST or one of username or password is missing
    return HttpResponseBadRequest()  '')'')
