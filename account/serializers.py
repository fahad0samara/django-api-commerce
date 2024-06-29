from rest_framework import serializers
from django.contrib.auth.models import User


class SingUpSerializer(serializers.ModelSerializer):
    class Meta:
        model= User
        fields=('password','email','first_name','last_name')
        extra_kwargs={
          'first_name':{'required':True,
            'allow_blank':False},
            'last_name':
            {'required':True,
            'allow_blank':False},
            'email':
            {'required':True,
            'allow_blank':False},
            'password':
            {'required':True,
            'allow_blank':False},
            'write_only':True,
            'min_length':8
        }


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        fields=('username','password','email','first_name','last_name')
        model= User

   
        
   


        




   

