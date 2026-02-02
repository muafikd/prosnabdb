# Generated migration: CrmDeal model + CommercialProposal.deal, client nullable

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('proposals', '0041_alter_equipmentphoto_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='CrmDeal',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID')),
                ('bitrix_deal_id', models.CharField(max_length=50, unique=True, verbose_name='ID сделки в Bitrix24')),
                ('title', models.CharField(max_length=500, verbose_name='Название сделки')),
                ('stage_id', models.CharField(blank=True, max_length=100, verbose_name='Статус (Stage)')),
                ('bitrix_company_id', models.CharField(blank=True, max_length=50, null=True, verbose_name='ID компании в Bitrix24')),
                ('bitrix_contact_id', models.CharField(blank=True, max_length=50, null=True, verbose_name='ID контакта в Bitrix24')),
                ('contact_name', models.CharField(blank=True, max_length=255, null=True, verbose_name='Имя контакта')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
                ('client', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='crm_deals',
                    to='proposals.client',
                    verbose_name='Локальный клиент (компания)',
                    db_column='client_id',
                )),
            ],
            options={
                'db_table': 'crm_deal_list',
                'verbose_name': 'Сделка Bitrix24',
                'verbose_name_plural': 'Сделки Bitrix24',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddField(
            model_name='commercialproposal',
            name='deal',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='commercial_proposals',
                to='proposals.crmdeal',
                verbose_name='Сделка Bitrix24',
                db_column='deal_id',
            ),
        ),
        migrations.AlterField(
            model_name='commercialproposal',
            name='client',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='commercial_proposals',
                to='proposals.client',
                verbose_name='Клиент',
                db_column='client_id',
            ),
        ),
    ]
