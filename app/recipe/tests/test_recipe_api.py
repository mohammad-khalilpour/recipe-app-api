from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from decimal import Decimal

from core.models import Recipe, Tag

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_recipe(user, **params):
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 5,
        'price': Decimal('5.50'),
        'description': 'Sample recipe description',
    }
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


def payload_sample():
    return {
        'title': 'Sample recipe',
        'time_minutes': 5,
        'price': Decimal('5.50'),
        'description': 'Sample recipe description',
        'tags': [{'name': 'foo'}, {'name': 'bar'}]
    }

class PublicRecipeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test@example.com',
            password='example123'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        other_user = get_user_model().objects.create_user(
            email='test2@example.com',
            password='example123'
        )
        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)

        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        payload = {
            'title': 'Sample recipe',
            'time_minutes': 5,
            'price': Decimal('5.50'),
            'description': 'Sample recipe description',
        }
        res = self.client.post(RECIPES_URL, payload)
        recipe = Recipe.objects.get(id=res.data['id'])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_create_recipe_with_new_tags(self):
        res = self.client.post(RECIPES_URL, payload_sample(), format='json')
        recipes = Recipe.objects.filter(user=self.user)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(recipes.count(), 1)
        self.assertEqual(recipes[0].tags.count(), 2)
        for tag in payload_sample()['tags']:
            exists = recipes[0].tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tag(self):
        test_tag = Tag.objects.create(user=self.user, name='bar')

        res = self.client.post(RECIPES_URL, payload_sample(), format='json')
        recipes = Recipe.objects.filter(user=self.user)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(recipes.count(), 1)
        self.assertEqual(recipes[0].tags.count(), 2)
        self.assertIn(test_tag, recipes[0].tags.all())
        for tag in payload_sample()['tags']:
            exists = recipes[0].tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update_recipe(self):
        recipe = create_recipe(user=self.user)
        payload = {'tags': [{'name': 'foo'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(name='foo', user=self.user)
        self.assertIn(new_tag, recipe.tags.all())

    def test_assign_tag_on_update_recipe(self):
        test_tag = Tag.objects.create(user=self.user, name='bar')
        test2_tag = Tag.objects.create(user=self.user, name='foo')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(test_tag)

        payload = {'tags': [{'name': 'foo'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, 'json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(test2_tag, recipe.tags.all())
        self.assertNotIn(test_tag, recipe.tags.all())

    def test_clear_recipe_tags(self):
        recipe = create_recipe(user=self.user)
        test_tag = Tag.objects.create(user=self.user, name='bar')
        recipe.tags.add(test_tag)
        payload = {'tags': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, 'json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)
