"""
Modified Django Views for PDF Generation

INSTALLATION:
  - Place pdf_filler.py at the SAME level as this views.py file
  - Then this import will work: from .pdf_filler import generate_form_pdf
  
REPLACE the existing TaxpayerFormRenderView class with the code below
ADD the TaxpayerFormPDFView class (it's new)
"""

import os
from django.http import HttpResponse
from django.shortcuts import redirect
from rest_framework import views
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer

# Import PDF filler utility (pdf_filler.py should be in the SAME directory as views.py)
from .pdf_filler import generate_form_pdf


class TaxpayerFormPDFView(views.APIView):
    """
    Generate EDITABLE PDF using PyMuPDF (Stage 3 pipeline logic)
    
    Endpoint: /api/v1/taxpayer/{taxpayer_id}/render/pdf/{year}/{pk}/
    
    This replaces the old PDF generation that created flat/non-editable PDFs
    """
    
    def get(self, request, taxpayer_id, year, pk):
        """
        Generate and return editable PDF for the specified form
        
        Args:
            taxpayer_id: ID of the taxpayer (40, 41, 42, etc.)
            year: Tax year (2025)
            pk: Form ID (16026 for Form 1040, etc.)
        
        Returns:
            HttpResponse with PDF content
        """
        try:
            # Get form instance from database
            form_instance = self.get_form(request, taxpayer_id, year, pk)
            
            # Generate editable PDF using PyMuPDF
            pdf_bytes = generate_form_pdf(form_instance)
            
            # Return PDF response
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="Form_{pk}_{year}.pdf"'
            
            return response
            
        except FileNotFoundError as e:
            return HttpResponse(
                f'Error: PDF template not found. {str(e)}',
                status=500
            )
        except ValueError as e:
            return HttpResponse(
                f'Error: Invalid form data. {str(e)}',
                status=400
            )
        except Exception as e:
            return HttpResponse(
                f'Error generating PDF: {str(e)}',
                status=500
            )
    
    def get_form(self, request, taxpayer_id, year, pk):
        """
        Get form instance from database
        
        TODO: Replace with your actual database query
        
        Example implementation:
        ```
        from .models import Form
        return Form.objects.get(
            id=pk,
            year=year,
            taxpayer_id=taxpayer_id
        )
        ```
        
        The returned object MUST have:
        - id: Form ID (e.g., 16026)
        - name: Form name (e.g., "FORM 1040")
        - data: JSON dict with structure:
            {
                "taxpayer": {"first_name": "...", "last_name": "...", "ssn": "..."},
                "fields": {"1a": {"value": "...", "can_be_modified": true}, ...}
            }
        """
        # TODO: Implement your database query here
        # For now, this is a placeholder
        raise NotImplementedError("Please implement get_form() method")


class TaxpayerFormRenderView(views.APIView):
    """
    Redirect HTML form view to PDF view
    
    Endpoint: /api/v1/taxpayer/{taxpayer_id}/render/form/{year}/{pk}/
    
    This used to render HTML forms with CSS positioning (formatting issues)
    Now it just redirects to the PDF endpoint
    """
    
    def get_renderers(self):
        return [TemplateHTMLRenderer()]
    
    def get(self, request, taxpayer_id, year, pk):
        """
        Redirect to PDF view
        
        Users clicking on forms in the review section will be redirected
        from HTML view to PDF view automatically
        """
        # Redirect to PDF endpoint
        pdf_url = f'/api/v1/taxpayer/{taxpayer_id}/render/pdf/{year}/{pk}/'
        return redirect(pdf_url)
        
        # ALL THE OLD HTML RENDERING CODE IS REMOVED!
        # No more:
        # - form_instance = self.get_form(...)
        # - template_name_path = self.get_template_path(...)
        # - context = {"form": form_instance, ...}
        # - return Response(context, template_name=...)


# OPTIONAL: If you want to support both HTML and PDF views
# (Keep HTML for editing, PDF for viewing)
class TaxpayerFormRenderView_HYBRID(views.APIView):
    """
    Hybrid approach: Support both HTML and PDF views
    
    Usage:
    - /render/form/2025/16026/           → Shows PDF (default)
    - /render/form/2025/16026/?format=html → Shows HTML (for editing)
    """
    
    def get_renderers(self):
        return [TemplateHTMLRenderer()]
    
    def get(self, request, taxpayer_id, year, pk):
        # Check if user wants HTML or PDF
        render_format = request.GET.get('format', 'pdf')  # Default to PDF
        
        if render_format == 'pdf':
            # Redirect to PDF endpoint
            pdf_url = f'/api/v1/taxpayer/{taxpayer_id}/render/pdf/{year}/{pk}/'
            return redirect(pdf_url)
        
        # Show HTML view (original code)
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
    
    def get_template_path(self, form_instance):
        """Your existing implementation"""
        # Copy your existing get_template_path() method here if using hybrid mode
        pass
    
    def get_form(self, request, taxpayer_id, year, pk):
        """Your existing implementation"""
        # Copy your existing get_form() method here
        pass
    
    def get_taxpayer(self, taxpayer_id):
        """Your existing implementation"""
        # Copy your existing get_taxpayer() method here
        pass


"""
INSTALLATION NOTES:

1. This file should REPLACE the existing views.py content
   OR you can merge these classes into your existing views.py

2. Make sure to import pdf_filler at the top:
   from .utils.pdf_filler import generate_form_pdf

3. Implement the get_form() method based on your database structure

4. If you want to keep HTML view for editing, use TaxpayerFormRenderView_HYBRID
   instead of TaxpayerFormRenderView
"""
