from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from ads.models import Ad, ExchangeProposal

User = get_user_model()


class ViewsCoverageTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.alice = User.objects.create_user(
            username='alice', password='pass')
        self.bob = User.objects.create_user(username='bob',   password='pass')
        self.ad1 = Ad.objects.create(
            user=self.alice, title='A1', description='Desc1',
            category='Cat1', condition='new'
        )
        self.ad2 = Ad.objects.create(
            user=self.bob, title='B1', description='Desc2',
            category='Cat2', condition='used'
        )
        self.prop = ExchangeProposal.objects.create(
            ad_sender=self.ad1, ad_receiver=self.ad2, comment='hi', status='waiting'
        )

    def test_login_get_and_post_invalid(self):
        url = reverse('login')
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        r2 = self.client.post(
            url, {'username': 'x', 'password': 'y'}, follow=True)
        self.assertContains(r2, "Неверное имя пользователя или пароль")

    def test_signup_get_and_post_invalid(self):
        url = reverse('signup')
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        r2 = self.client.post(url, {
            'username': 'new', 'password1': '123', 'password2': '456'
        }, follow=True)
        self.assertContains(r2, "Проверьте введённые данные")

    def test_logout_redirects(self):
        self.client.login(username='alice', password='pass')
        r = self.client.get(reverse('logout'), follow=True)
        self.assertRedirects(r, reverse('ad_list'))

    def test_ad_list_filters(self):
        r = self.client.get(reverse('ad_list') + '?q=A1')
        self.assertContains(r, 'A1')
        self.assertNotContains(r, 'B1')
        r2 = self.client.get(reverse('ad_list') + '?category=Cat2')
        self.assertContains(r2, 'B1')
        self.assertNotContains(r2, 'A1')
        r3 = self.client.get(reverse('ad_list') + '?condition=new')
        self.assertContains(r3, 'A1')
        self.assertNotContains(r3, 'B1')

    def test_ad_detail_404(self):
        self.assertEqual(self.client.get('/ads/9999/').status_code, 404)

    def test_ad_create_form_invalid_and_valid(self):
        self.client.login(username='alice', password='pass')
        url = reverse('ad_create')
        r = self.client.post(url, {}, follow=True)
        self.assertContains(r, "Не удалось создать объявление")
        data = {
            'title': 'C1', 'description': 'D', 'category': 'X', 'condition': 'new'
        }
        r2 = self.client.post(url, data, follow=True)
        self.assertContains(r2, 'C1')
        self.assertTrue(Ad.objects.filter(title='C1').exists())

    def test_ad_update_not_owner_and_form_invalid(self):
        self.client.login(username='bob', password='pass')
        url = reverse('ad_update', kwargs={'pk': self.ad1.pk})
        r = self.client.get(url)
        self.assertEqual(r.status_code, 403)
        self.client.login(username='alice', password='pass')
        r2 = self.client.post(
            url, {'title': '', 'description': '', 'category': '', 'condition': ''}, follow=True)
        self.assertContains(r2, "Не удалось обновить объявление")

    def test_ad_delete_not_owner(self):
        self.client.login(username='bob', password='pass')
        url = reverse('ad_delete', kwargs={'pk': self.ad1.pk})
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_proposal_form_context_and_invalid(self):
        self.client.login(username='alice', password='pass')
        url = reverse('proposal_create', kwargs={'pk': self.ad2.pk})
        r = self.client.get(url)
        self.assertContains(r, 'Предложить обмен по объявлению «B1»')
        r2 = self.client.post(
            url, {'ad_sender': self.ad2.pk, 'comment': 'x'}, follow=True)
        self.assertContains(r2, "Не удалось создать предложение обмена")

    def test_proposal_create_valid(self):
        self.client.login(username='alice', password='pass')
        url = reverse('proposal_create', kwargs={'pk': self.ad2.pk})
        r = self.client.post(
            url, {'ad_sender': self.ad1.pk, 'comment': 'hey'}, follow=True)
        self.assertContains(r, "Предложение создано")
        self.assertTrue(ExchangeProposal.objects.filter(
            ad_sender=self.ad1, ad_receiver=self.ad2).exists())

    def test_proposal_list_view_type_and_filters(self):
        self.client.login(username='alice', password='pass')
        base = reverse('proposal_list')
        r_all = self.client.get(base + '?type=all')
        self.assertContains(r_all, 'A1 → B1')
        r_sent = self.client.get(base + '?type=sent')
        self.assertContains(r_sent, 'A1 → B1')
        r_rec = self.client.get(base + '?type=received')
        self.assertNotContains(r_rec, 'A1 → B1')
        self.client.login(username='bob', password='pass')
        r_rec2 = self.client.get(base + '?type=received')
        self.assertContains(r_rec2, 'A1 → B1')
        r_s = self.client.get(base + '?sender=alice')
        self.assertContains(r_s, 'A1 → B1')
        r_r = self.client.get(base + '?receiver=bob')
        self.assertContains(r_r, 'A1 → B1')
        r_st = self.client.get(base + '?status=waiting')
        self.assertContains(r_st, 'A1 → B1')

    def test_proposal_detail_permission(self):
        charlie = User.objects.create_user(username='charlie', password='pass')
        self.client.login(username='charlie', password='pass')
        self.assertEqual(self.client.get(
            reverse('proposal_detail', kwargs={'pk': self.prop.pk})).status_code, 403)
        for u in ('alice', 'bob'):
            self.client.login(username=u, password='pass')
            r = self.client.get(
                reverse('proposal_detail', kwargs={'pk': self.prop.pk}))
            self.assertEqual(r.status_code, 200)

    def test_proposal_update_status_not_receiver(self):
        self.client.login(username='alice', password='pass')
        url = reverse('proposal_update_status', kwargs={
                      'pk': self.prop.pk, 'action': 'accept'})
        r = self.client.post(url, follow=True)
        self.assertContains(r, "Только получатель может изменить статус")

    def test_proposal_update_status_invalid_action(self):
        self.client.login(username='bob', password='pass')
        url = reverse('proposal_update_status', kwargs={
                      'pk': self.prop.pk, 'action': 'foo'})
        r = self.client.post(url, follow=True)
        self.assertContains(r, "Неверное действие")

    def test_proposal_update_status_accept_and_reject(self):
        self.client.login(username='bob', password='pass')
        url_rej = reverse('proposal_update_status', kwargs={
                          'pk': self.prop.pk, 'action': 'reject'})
        self.client.post(url_rej, follow=True)
        self.prop.refresh_from_db()
        self.assertEqual(self.prop.status, 'rejected')
        self.prop.status = 'waiting'
        self.prop.save()
        url_acc = reverse('proposal_update_status', kwargs={
                          'pk': self.prop.pk, 'action': 'accept'})
        self.client.post(url_acc, follow=True)
        self.prop.refresh_from_db()
        self.ad1.refresh_from_db()
        self.ad2.refresh_from_db()
        self.assertEqual(self.prop.status, 'accepted')
        self.assertEqual(self.ad1.user, self.bob)
        self.assertEqual(self.ad2.user, self.alice)
