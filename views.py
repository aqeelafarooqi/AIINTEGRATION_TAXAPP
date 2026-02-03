import os

from django.conf import settings
from rest_framework import views
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer


class TaxpayerFormRenderView(views.APIView):

    def get_renderers(self):
        return [TemplateHTMLRenderer()]

    def get_template_path(self, form_instance):
        template_name_base = form_instance.name.lower().replace(" ", "_")
        template_name_path = f"forms/{template_name_base}.html"

        templates_dir = os.path.join(settings.BASE_DIR, "templates")
        full_template_path = os.path.join(templates_dir, template_name_path)

        if not os.path.exists(full_template_path):
            generic_form_template_path = "forms/form.html"
            if os.path.exists(os.path.join(templates_dir, generic_form_template_path)):
                template_name_path = generic_form_template_path
            else:
                template_name_path = "forms/form_1040.html"

        return template_name_path

    def get(self, request, taxpayer_id, year, pk):
        form_instance = self.get_form(request, taxpayer_id, year, pk)
        template_name_path = self.get_template_path(form_instance)
        taxpayer = self.get_taxpayer(taxpayer_id)

        context = {
            "form": form_instance,
            "year": year,
            "taxpayer": taxpayer,
            "user": request.user,
            "dependents": taxpayer.dependent_set.all() if taxpayer else [],
        }

        return Response(context, template_name=template_name_path)
