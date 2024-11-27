import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse

from .models import *


def index(request):
    return render(request, "network/index.html")


def login_view(request):
    if request.method == "POST":

        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")


def profile(request, username):
    try:
        requested_user = User.objects.get(username = username)
    except User.DoesNotExist:
        return JsonResponse({"error": f"{username} doesn't exist"}, status=400)
        
    return render(request, "network/profile.html", {
        "requested_user": requested_user,
    })


@login_required
def following(request):
    return render(request, "network/following.html")


@login_required
def new_post(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400) 
    
    data = json.loads(request.body)
    post_text = data.get('postText', '')
    
    Post.objects.create(user = request.user,
                        text = post_text)
    
    return JsonResponse({"message": "Post created successfully."}, status=201)


def posts(request):
    username = request.GET.get("username") or ""
    start_i = int(request.GET.get("start") or 0)
    end_i = int(request.GET.get("end") or (start_i + 10))

    if username:
        try:
            requested_user = User.objects.get(username = username)
        except User.DoesNotExist:
            return JsonResponse({"error": f"{username} doesn't exist"}, status=400)
        
        requested_posts = Post.objects.filter(user = requested_user).order_by("-timestamp")[start_i:end_i]

    else:
        requested_posts = Post.objects.all().order_by("-timestamp")[start_i:end_i]
    
    return JsonResponse([post.serialize() for post in requested_posts], safe=False, status=201)


@login_required
def posts_following(request):
    start_i = int(request.GET.get("start") or 0)
    end_i = int(request.GET.get("end") or (start_i + 10))

    requested_following = Follower.objects.filter(follower = request.user)

    if requested_following:
        requested_users = [follower.following for follower in requested_following]
    else:
        JsonResponse([], safe=False, status=201)

    if requested_users:
        requested_posts = Post.objects.filter(user__in = requested_users).order_by("-timestamp")[start_i:end_i]
    else:
        JsonResponse([], safe=False, status=201)

    return JsonResponse([post.serialize() for post in requested_posts], safe=False, status=201)


def iscreator(request, post_id):
    try:
        requested_post = Post.objects.get(id = post_id)
    except Post.DoesNotExist:
        return JsonResponse({"error": f"Post {post_id} doesn't exist"}, status=400)
    
    if request.user == requested_post.user:
        return JsonResponse({"iscreator": True}, status=201)
    else:
        return JsonResponse({"iscreator": False}, status=201)


def post_edit(request, post_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400) 
    
    try:
        requested_post = Post.objects.get(id = post_id)
    except Post.DoesNotExist:
        return JsonResponse({"error": f"Post {post_id} doesn't exist"}, status=400)
    
    if requested_post.user != request.user:
        return JsonResponse({"error": "Only post creator can edit the post"}, status=400) 
    
    data = json.loads(request.body)
    post_text = data.get('newText', '')
    
    requested_post.text = post_text
    requested_post.save()

    return JsonResponse({"updated": True}, status=201)


def count_posts(request):
    username = request.GET.get("username") or ""

    if username:
        try:
            requested_user = User.objects.get(username = username)
        except User.DoesNotExist:
            return JsonResponse({"error": f"{username} doesn't exist"}, status=400)

        posts_count = Post.objects.filter(user = requested_user).count()

        return JsonResponse({"posts_count": posts_count}, status=201)
    
    else:
        posts_count = Post.objects.all().count()

        return JsonResponse({"posts_count": posts_count}, status=201)


@login_required
def count_posts_following(request):
    requested_following = Follower.objects.filter(follower = request.user)

    if requested_following:
        requested_users = [follower.following for follower in requested_following]
    else:
        JsonResponse([], safe=False, status=201)

    if requested_users:
        posts_count = Post.objects.filter(user__in = requested_users).count()
        return JsonResponse({"posts_count": posts_count}, status=201)
    else:
        JsonResponse([], safe=False, status=201)

    return JsonResponse({"posts_count": posts_count}, status=201)


@login_required
def isfollowing(request, username):
    try:
        requested_user = User.objects.get(username = username)
    except User.DoesNotExist:
        return JsonResponse({"error": f"{username} doesn't exist"}, status=400)
    
    try:
        Follower.objects.get(follower = request.user, following = requested_user)
    except Follower.DoesNotExist:
        return JsonResponse({"isfollowing": False}, status=201)
    
    return JsonResponse({"isfollowing": True}, status=201)


def count_following(request, username):
    try:
        requested_user = User.objects.get(username = username)
    except User.DoesNotExist:
        return JsonResponse({"error": f"{username} doesn't exist"}, status=400)

    following_count = Follower.objects.filter(follower = requested_user).count()

    return JsonResponse({"following_count": following_count}, status=201)


def count_followers(request, username):
    try:
        requested_user = User.objects.get(username = username)
    except User.DoesNotExist:
        return JsonResponse({"error": f"{username} doesn't exist"}, status=400)

    followers_count = Follower.objects.filter(following = requested_user).count()

    return JsonResponse({"followers_count": followers_count}, status=201)
    

@login_required
def follow(request, username):
    if request.method != 'POST':
        return JsonResponse({"error": "POST request required."}, status=400)
    
    try:
        requested_user = User.objects.get(username = username)
    except User.DoesNotExist:
        return JsonResponse({"error": f"{username} doesn't exist"}, status=400)
    
    get_follower, create_follower = Follower.objects.get_or_create(follower = request.user, following = requested_user)

    if get_follower or create_follower:
        return JsonResponse({"isfollowing": True}, status=201)
    
    return JsonResponse({"isfollowing": False}, status=201)
        
    
@login_required
def unfollow(request, username):
    if request.method != 'POST':
        return JsonResponse({"error": "POST request required."}, status=400) 
    
    try:
        requested_user = User.objects.get(username = username)
    except User.DoesNotExist:
        return JsonResponse({"error": f"{username} doesn't exist"}, status=400)
    
    try:
        follower = Follower.objects.get(follower = request.user, following = requested_user)
        follower.delete()
    except Follower.DoesNotExist:
        return JsonResponse({"isfollowing": False}, status=201)
    
    return JsonResponse({"isfollowing": False}, status=201)


def count_likes(request, post_id):
    try:
        requested_post = Post.objects.get(id = post_id)
    except Post.DoesNotExist:
        return JsonResponse({"error": f"Post {post_id} doesn't exist"}, status=400)

    likes_count = Like.objects.filter(post = requested_post).count()

    return JsonResponse({"likes_count": likes_count}, status=201)
    

@login_required
def isliked(request, post_id):
    try:
        requested_post = Post.objects.get(id = post_id)
    except Post.DoesNotExist:
        return JsonResponse({"error": f"Post {post_id} doesn't exist"}, status=400)
    
    try:
        requested_post = Like.objects.get(user = request.user, post = requested_post)
    except Like.DoesNotExist:
        return JsonResponse({"liked": False}, status=201)
    
    return JsonResponse({"liked": True}, status=201)


@login_required
def like(request, post_id):
    if request.method != 'POST':
        return JsonResponse({"error": "POST request required."}, status=400) 
    
    try:
        requested_post = Post.objects.get(id = post_id)
    except Post.DoesNotExist:
        return JsonResponse({"error": f"Post {post_id} doesn't exist"}, status=400)
    
    get_like, create_like = Like.objects.get_or_create(user = request.user, post = requested_post)

    if get_like or create_like:
        return JsonResponse({"liked": True}, status=201)
    
    return JsonResponse({"liked": False}, status=201)


@login_required
def unlike(request, post_id):
    if request.method != 'POST':
        return JsonResponse({"error": "POST request required."}, status=400) 
    
    try:
        requested_post = Post.objects.get(id = post_id)
    except Post.DoesNotExist:
        return JsonResponse({"error": f"Post {post_id} doesn't exist"}, status=400)
    
    try:
        delete_like = Like.objects.get(user = request.user, post = requested_post)
        delete_like.delete()
    except Like.DoesNotExist:
        return JsonResponse({"liked": False}, status=201)
    
    return JsonResponse({"liked": False}, status=201)