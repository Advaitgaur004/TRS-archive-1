from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import render, get_object_or_404
from api.models import User, Post, Comment, New, Review
from api.serializer import ReviewSerializer

from rest_framework import status,generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.serializer import *
from rest_framework import status
from rest_framework.generics import CreateAPIView, GenericAPIView, ListAPIView, mixins, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
import os
from django.conf import settings
import datetime
from django.db import IntegrityError
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail, EmailMultiAlternatives


from ..models import *





@api_view(['GET'])
@permission_classes([IsAuthenticated])
def UserReviewsParticularPost(request,post_id):
    reviews = Review.objects.filter(post_id=post_id,for_user=True).order_by('-created_at')
    serializer=ReviewSerializer(reviews,many=True) 
    return Response(serializer.data, status=status.HTTP_200_OK)

class ReviewsParticularPost(GenericAPIView, mixins.ListModelMixin):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, post_id, *args, **kwargs):
        post = Post.objects.get(id=post_id)
        reviews = Review.objects.filter(post_id=post_id)
        serializer = self.serializer_class(reviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class EditorToUserReviewView(GenericAPIView, mixins.CreateModelMixin):
    '''This Class is used to post review to user by Editor'''
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]


    def post(self, request, *args, **kwargs):
        user = request.user
        # print(user, user.roles)
        if user.roles != 'editor':
            return Response("You are not authorized to create a review", status=status.HTTP_401_UNAUTHORIZED)
        
        post = Post.objects.get(id=request.data.get('post_id'))
        
        if 'description' not in request.data:
            return Response("Description must be provided", status=status.HTTP_400_BAD_REQUEST)
        
        print(request.data.get('description'))
        reviewed_pdf = request.FILES.get('reviewed_pdf')
        print(reviewed_pdf)
        try:
            review_data={
                'description': request.data.get('description'),
                'pdf_file_status' : 'Reviewed',
                'reviewer' : user,
                'editor' : user, 
                'is_reviewed' : True,
                'post' : post,
                'for_user' : True
            }
            if reviewed_pdf:
                print(reviewed_pdf)
                review_data['reviewed_pdf'] = reviewed_pdf

            review = Review.objects.create(**review_data)
            review.save()
            post.status=request.data.get('status')
            Send_Mail_to_User(review.id)
            post.save()
            return Response("Review created successfully", status=status.HTTP_201_CREATED)

        except IntegrityError as e:
            return Response("IntegrityError: {}".format(str(e)), status=status.HTTP_400_BAD_REQUEST)

class EditorReviewListView(GenericAPIView,mixins.ListModelMixin, mixins.UpdateModelMixin, mixins.CreateModelMixin):
    '''
    This class is used to create, update and list reviews for a post specified by post_id and for editor users only
    '''
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # print("the role is ",request.user.roles)
        if request.user.roles != 'editor':
            return Response("You are not authorized to Fetch this review", status=status.HTTP_401_UNAUTHORIZED)
        editor = request.user
        reviews = Review.objects.filter(editor_id=editor.id,is_reviewed=False)
        serializer = self.serializer_class(reviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request,post_id,reviewer_id, *args, **kwargs):
        post = Post.objects.get(id=post_id)
        review = Review.objects.get(post_id = post_id,reviewer_id=reviewer_id, editor_id=request.user.id)
        if request.user.roles != 'editor' and request.user.roles != 'admin':
            return Response("You are not authorized to update this review", status=status.HTTP_401_UNAUTHORIZED)
        if 'description' in request.data:
            review.description = request.data['description']
        if 'pdf_file_status' in request.data:
            new_status = request.data['pdf_file_status']
            if new_status in dict(Status_Choices).keys():
                review.pdf_file_status = new_status
            else:
                return Response("Invalid PDF file status provided", status=status.HTTP_400_BAD_REQUEST)
        if 'is_reviewed' in request.data:
            review.is_reviewed = request.data['is_reviewed']

        review.save()
        return Response("Review updated successfully", status=status.HTTP_200_OK)
    
    def post(self, request, post_id, *args, **kwargs):
        user = request.user
        if user.roles != "editor":
            # print(user.roles)
            return Response("You are not authorized to create a review", status=status.HTTP_401_UNAUTHORIZED)
        post = Post.objects.get(id=post_id)
        reviewer= User.objects.get(username=request.data.get('reviewer'))

        # if 'description' not n request.data:
        #     return Response("Description must be provided", status=status.HTTP_400_BAD_REQUEST)
        # if 'pdf_file_status' not in request.data:
        #     return Response("pdf_file_status must be provided", status=status.HTTP_400_BAD_REQUEST)
      
        try:
            review = Review.objects.create(
                # description = request.data['description'],
                # pdf_file_status = request.data['pdf_file_status'],
                reviewer =reviewer,
                editor=user,
                is_reviewed = False,
                post = post
                )
            review.save()
            post.status='Under_Review'
            post.save()
            print(post.status)
            Send_Mail_to_Reviewer(review.id)

        except IntegrityError as e:
            return Response("IntegrityError: {}".format(str(e)), status=status.HTTP_400_BAD_REQUEST)   

        
        serializer = self.serializer_class(review)
        return Response(serializer.data, status=status.HTTP_201_CREATED)



class ParticularReviewviewSet(GenericAPIView, mixins.RetrieveModelMixin):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, review_id, *args, **kwargs):
        if request.user.roles not in ['reviewer', 'editor']:
            return Response("You are not authorized to Fetch this review", status=status.HTTP_401_UNAUTHORIZED)
        review = Review.objects.get(id=review_id[1:])
        serializer = self.serializer_class(review)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    def put(self,request,review_id,*args,**kwargs):
        
        if request.user.roles != 'reviewer':
            return Response("You are not authorized to Fetch this review", status=status.HTTP_401_UNAUTHORIZED)

        review=Review.objects.get(id=review_id)
        data=request.data

        
        review.description=data['desc']
        # print(data['reviewed_pdf'])
        if 'reviewed_pdf' in data :
            review.reviewed_pdf= data['reviewed_pdf']
        
        if(data['is_reviewed']=="false"):
            bool_output=False
        else:
            bool_output=True
        
        if 'pdf_file_status' in data and data['pdf_file_status']:
            print(data['pdf_file_status'])
            review.pdf_file_status=data['pdf_file_status']
        

        if(review.is_reviewed!=bool_output and review.is_reviewed==False):  #is reviwed changed from false to true
            review.is_reviewed=bool_output
            review.save()
            Send_Mail_to_Editor(review_id)
        else:
            review.is_reviewed=bool_output
            review.save()
        
        

        
        serializer = self.serializer_class(review)
        return Response(serializer.data, status=status.HTTP_200_OK)

        
class ReviewerReviewViewset(GenericAPIView, mixins.ListModelMixin, mixins.UpdateModelMixin):
    '''
This class is used to list and update reviews for a post specified by post_id and for reviewer users only
    '''
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if request.user.roles != 'reviewer':
            return Response("You are not authorized to Fetch this review", status=status.HTTP_401_UNAUTHORIZED)
        reviewer = request.user
        reviews = Review.objects.filter(reviewer_id=reviewer.id,is_reviewed=False)
        serializer = self.serializer_class(reviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, post_id, editor_id, *args, **kwargs):
        
        if request.user.roles != 'reviewer':
            return Response("You are not authorized to Fetch this review", status=status.HTTP_401_UNAUTHORIZED)
        
        post = Post.objects.get(id=post_id)

        review = Review.objects.get(post_id=post_id, reviewer_id=request.user.id, editor_id=editor_id)
        if request.user.roles != 'reviewer' and request.user.roles != 'admin':
            return Response("You are not authorized to update this review", status=status.HTTP_401_UNAUTHORIZED)

        if 'pdf_file_status' in request.data:
            new_status = request.data['pdf_file_status']
            if new_status in dict(Status_Choices).keys():
                review.pdf_file_status = new_status
            else:
                return Response("Invalid PDF file status provided", status=status.HTTP_400_BAD_REQUEST)

        if request.FILES.get('reviewed_pdf'):
            review.reviewed_pdf = request.FILES.get('reviewed_pdf')
            review.is_reviewed = True

            

        review.save()
        return Response("Review updated successfully", status=status.HTTP_200_OK)
    


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def GetReviewedReviews(request):
    user=request.user
    print(user.roles)
    if user.roles not in ['reviewer', 'editor']:
            return Response("You are not authorized to Fetch this review", status=status.HTTP_401_UNAUTHORIZED)
    

    if user.roles=='reviewer':
        reviews = Review.objects.filter(reviewer_id=user.id,is_reviewed=True)
    else:
        reviews = Review.objects.filter(editor_id=user.id,is_reviewed=True,for_user=False)

    serializer=ReviewSerializer(reviews,many=True) 
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def GetEditorReviews(request):
    user=request.user
    print(user.roles)
    if user.roles not in ['reviewer', 'editor']:
            return Response("You are not authorized to Fetch this review", status=status.HTTP_401_UNAUTHORIZED)
    

    if user.roles=='editor':
        reviews = Review.objects.filter(reviewer_id=user.id,is_reviewed=True,for_user=True)


    serializer=ReviewSerializer(reviews,many=True) 
    return Response(serializer.data, status=status.HTTP_200_OK)



def Send_Mail_to_User(review_id):
    try:
        review=Review.objects.get(id=review_id)
        post_id=review.post.id
        user_email=review.post.user.email

        try:
            post = Post.objects.get(id=post_id) 
        except Post.DoesNotExist:
            return Response(message,status=status.HTTP_400_BAD_REQUEST)
        
        subject = f'Regarding response of the review of Post:{post.title}'
        message = (f'Dear User,\n\n'
            f'I hope this message finds you well. I am writing to provide my review of the post titled "{post.title}". '
            f'Below, you will find my detailed review:\n\n'
            f'{review.description}\n\n'
            f'My feedback on this review is: {review.pdf_file_status}\n\n'
            f'Thank you and Best regards.\n\n'
            f'{review.editor.username}'
        )
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [user_email]

        email_message = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=from_email,
                to=recipient_list
            )
        
        # file_path=review.reviewed_pdf.path
        
        # Send the email
        # file_name = os.path.basename(file_path)
        # with open(file_path, 'rb') as f:
        #     email_message.attach(file_name, f.read(), 'application/pdf')  # Adjust content type as needed

        email_message.send()
        
        return Response("Email sended to reviewers successfully", status=status.HTTP_201_CREATED)


    except Exception as e:
        message = {'detail': str(e)}  # Return specific error message
        print(message)
        return Response(message, status=status.HTTP_400_BAD_REQUEST)
    






















def Send_Mail_to_Editor(review_id):
    try:
        review=Review.objects.get(id=review_id)
        editor_email=review.editor.email
        post_id=review.post.id
        
        try:
            post = Post.objects.get(id=post_id) 
        except Post.DoesNotExist:
            return Response(message,status=status.HTTP_400_BAD_REQUEST)
        
        subject = f'Regarding response of the review of Post:{post.title}'
        message = (f'Dear Editor,\n\n'
            f'I hope this message finds you well. I am writing to provide my review of the post titled "{post.title}". '
            f'Below, you will find my detailed review:\n\n'
            f'{review.description}\n\n'
            f'My feedback on this review is: {review.pdf_file_status}\n\n'
            f'Please let me know if there are any further actions required on my part.\n\n'
            f'Thank you for the opportunity to review this post.\n\n'
            f'Best regards,\n'
            f'{review.reviewer.username}'
        )
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [editor_email]

        email_message = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=from_email,
                to=recipient_list
            )
        
        # file_path=review.reviewed_pdf.path
        
        # Send the email
        # file_name = os.path.basename(file_path)
        # with open(file_path, 'rb') as f:
        #     email_message.attach(file_name, f.read(), 'application/pdf')  # Adjust content type as needed

        email_message.send()
        
        return Response("Email sended to reviewers successfully", status=status.HTTP_201_CREATED)


    except Exception as e:
        message = {'detail': str(e)}  # Return specific error message
        print(message)
        return Response(message, status=status.HTTP_400_BAD_REQUEST)
    



def Send_Mail_to_Reviewer(review_id):

    #this function gets input of the email_id and post
    try:
        review=Review.objects.get(id=review_id)
        reviewer_email=review.reviewer.email
        post_id=review.post.id
        
        
        try:
            post = Post.objects.get(id=post_id) 
        except Post.DoesNotExist:
            return Response(message,status=status.HTTP_400_BAD_REQUEST)
        
        subject = f'Assignment of Review: {post.title}'
        message = f'''
Dear {review.reviewer.username},

You have been assigned to review the following research paper:

Title: {post.title}
Content: {post.body}

Please complete your review for above research.

Best regards,
{review.editor.username}
Editor

Note: This email contains the confidential content of the research paper. Please do not share it with anyone outside the review process.'''
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [reviewer_email]

        email_message = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=from_email,
                to=recipient_list
            )
        
        file_path=post.document.path
        
        # Send the email
        file_name = os.path.basename(file_path)
        with open(file_path, 'rb') as f:
            email_message.attach(file_name, f.read(), 'application/pdf')  # Adjust content type as needed

        email_message.send()
        
        return Response("Email sended to reviewers successfully", status=status.HTTP_201_CREATED)


    except Exception as e:
        message = {'detail': str(e)}  # Return specific error message
        print(message)
        return Response(message, status=status.HTTP_400_BAD_REQUEST)


