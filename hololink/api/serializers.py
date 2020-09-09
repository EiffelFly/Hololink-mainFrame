from django.contrib.auth.models import User, Group
from article.models import Article
from project.models import Project
from rest_framework import serializers
from django.shortcuts import get_object_or_404
from django.http import Http404
import hashlib
from django.utils import timezone

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        ordering = ['-created_at']
        model = Project
        fields = [
            'id','name', 'created_at', 'created_by', 'articles_project_owned',
            'project_basestone_keyword_sum', 'project_stellar_keyword_sum'
        ]
        read_only_fields = [
            'id', 'created_at', 'created_by'
        ]
        extra_kwargs = {'books': {'required': False}}

class ProjectSerializerForPost(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            'name'
        ]

class ArticleSerializer(serializers.ModelSerializer):
    '''
        Because the behavior of nested creates and updates can be ambiguous, and may require 
        complex dependencies between related models, REST framework 3 requires you to always 
        write these methods explicitly.

        https://www.django-rest-framework.org/api-guide/serializers/#writable-nested-representations
    '''
    projects = ProjectSerializer(many=True, read_only=True)

    class Meta:
        ordering = ['-created_at']
        model = Article
        fields = [
            'hash', 'name', 'content', 'from_url',
            'recommended', 'projects', 'created_by', 'created_at',
            'article_basestone_keyword_sum','article_stellar_keyword_sum','tokenize_output','ner_output',
            'final_output'
        ]
        read_only_fields = [
            'hash', 'created_at', 'created_by'
        ]
        extra_kwargs = {'authors': {'required': False}}


class ArticleSerializerForNEREngine(serializers.ModelSerializer):

    ner_output = serializers.JSONField()

    class Meta:
        model = Article
        fields = [
            'name', 'from_url','D3_data_format', 'ner_output',
        ]
        read_only_fields = [
            'D3_data_format'
        ]

    def create(self, validated_data):
        name = validated_data.get('name', None)
        from_url = validated_data.get('from_url', None)
        ner_output = validated_data.get('ner_output', None)
        
        try:
            article = Article.objects.get(name=name, from_url=from_url)
        except Article.DoesNotExist:
            raise serializers.ValidationError({"ValidationError": "Article doesn't exist, you must post exact the same name and url"})

        d3_data = json_to_d3(ner_output)   
        setattr(article, 'ner_output', ner_output)
        setattr(article, 'D3_data_format', d3_data)
        article.save()

        return article
        
        

class ArticleSerializerForPost(serializers.ModelSerializer):

    '''
        We use validate() method to check whether an article is duplicated in the galaxy
        then we use create() method to get the existing object and update it or create it.

        *many to many fields will first be removed from fieldlist by DRF.
    '''

    class Meta:
        model = Article
        fields = [
            'name', 'content', 'from_url',
            'recommended','projects',
        ]

    def validate(self, data):
        duplication_list = []
        username = self.context['request'].user
        user = get_object_or_404(User, username=username)
        for project in data['projects']:  
            try:
                article = get_object_or_404(Article, from_url=data['from_url'], projects=project, owned_by=user) # owned_by=user this can work!
                duplication_list.append(project)
            except Http404:
                pass

        if duplication_list:
            raise serializers.ValidationError({"Duplication Error": duplication_list})
        
        return data

    def create(self, validated_data):
        username = self.context['request'].user
        user = get_object_or_404(User, username=username)
        name = validated_data.get('name', None)
        from_url = validated_data.get('from_url', None)
        content = validated_data.get('content', None)
        recommended = validated_data.get('recommended', None)
        projects = validated_data.get('projects', None)
        
        try:
            article = Article.objects.get(name=name, from_url=from_url)
            for project in projects:
                try:
                    target_project = Project.objects.get(name=project, created_by=username)
                    article.projects.add(target_project)
                except Project.DoesNotExist:
                    print('There is no such project')
            if user not in article.owned_by.all():
                article.owned_by.add(user)
            return article

        except Article.DoesNotExist:

            data = {
                'hash':sha256_hash(content),
                'name':name,
                'from_url':from_url,
                'content':content,
                'recommended':recommended,
                'created_by':user,
                'created_at':timezone.localtime(timezone.now())
            }

            article = super().create(data)
            
            for project in projects:
                try:
                    target_project = Project.objects.get(name=project, created_by=username)
                    article.projects.add(target_project)
                except Project.DoesNotExist:
                    print('There is no such project')
            article.owned_by.add(user)
            return article

    
def sha256_hash(content):
    sha = hashlib.sha256()
    sha.update(content.encode())
    return sha.hexdigest()

def json_to_d3(data):

    
    article_title = data['title']
    article_galaxy = data['galaxy']
    article_url = data['url']

    nodejson = []
    basestoneNum = 0
    stellarNum = 0
    nodevalidator = []

    for key,value in data['Final'].items():
        title = value['Title']
        frequency = value['Frequency']
        keyword_type = value['POS']

        if keyword_type == 'Na' or keyword_type == 'Nb' or keyword_type == 'Nc':            
            nodejson.append({"title":title, "frequency":frequency, "group":"stellar", "type":keyword_type})
            stellarNum += 1
            nodevalidator.append(title)
        else:
            if keyword_type == 'DATE' or keyword_type == 'ORDINAL' or keyword_type == 'CARDINAL':
                pass
            else:
                nodejson.append({"title":title, "frequency":frequency, "group":"basestone", "type":keyword_type})
                basestoneNum += 1
                nodevalidator.append(title)


    processed_data = {
        "article":article_title, 
        "galaxy":article_galaxy, 
        "url":article_url, 
        "basestoneNum":basestoneNum, 
        "stellarNum":stellarNum, 
        "nodes":nodejson,
        "nodesvlaidator": nodevalidator,
    }

    return processed_data