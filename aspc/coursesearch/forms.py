from django import forms
from aspc.coursesearch.models import Department, Course, Meeting, CAMPUSES, CAMPUSES_LOOKUP
from django.db.models import Count


import re
from django.forms.widgets import Widget, Select
from django.utils.safestring import mark_safe

class DeptModelChoice(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return "%s - %s" % (obj.code, obj.name)

TIME_INPUT_FORMATS = [
    '%H:%M:%S',
    '%H:%M',
    '%I:%M%p',
    '%I:%M %p',
]

POSSIBLE_CREDIT = (('A', 'any'), ('F', 'full'), ('P', 'partial'), (0.0, '0.0'), (0.25, '0.25'), (0.5, '0.5'), (1.0, '1.0'), (1.5, '1.5'), (2.0, '2.0'), (3.0, '3.0'), (4.0, '4.0'), (6.0, '6.0'))

keyword_regex = re.compile(r'(\w+)')

class SearchForm(forms.Form):
    department = DeptModelChoice(queryset=Department.objects.annotate(num_courses=Count('course_set')).filter(num_courses__gt=0).distinct().order_by('code'), \
        required=False, empty_label="(any)")
    only_at_least = forms.ChoiceField(choices=(('A', 'at least'), ('O', 'only'),))
    m = forms.BooleanField(required=False)
    t = forms.BooleanField(required=False)
    w = forms.BooleanField(required=False)
    r = forms.BooleanField(required=False)
    f = forms.BooleanField(required=False)
    
    instructor = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'size':'40'}))
    min_class_size = forms.IntegerField(required=False, widget=forms.TextInput(attrs={'size':'3'}))
    credit = forms.ChoiceField(choices=POSSIBLE_CREDIT)
    
    start_range = forms.TimeField(required=False, input_formats=TIME_INPUT_FORMATS, widget=forms.TextInput(attrs={'size':'10'})) #widget=SelectTimeWidget(twelve_hr=True, use_seconds=False))
    end_range = forms.TimeField(required=False, input_formats=TIME_INPUT_FORMATS, widget=forms.TextInput(attrs={'size':'10'})) #widget=SelectTimeWidget(twelve_hr=True, use_seconds=False))
    
    c_cgu = forms.BooleanField(required=False)
    c_cm = forms.BooleanField(required=False)
    c_cu = forms.BooleanField(required=False)
    c_hm = forms.BooleanField(required=False)
    c_po = forms.BooleanField(required=False)
    c_pz = forms.BooleanField(required=False)
    c_sc = forms.BooleanField(required=False)
    
    keywords = forms.CharField(max_length=100, required=False)
    
    def clean(self):
        cleaned_data = self.cleaned_data
        if self._errors:
            return cleaned_data # user has to fix field errors first
        if not any(map(cleaned_data.get, ('m', 't', 'w', 'r', 'f', 'instructor', 'min_class_size',\
            'start_range', 'end_range', 'c_cgu', 'c_cm', 'c_cu', 'c_hm', 'c_po', 'c_pz', 'c_sc',\
            'department', 'keywords'))):
            raise forms.ValidationError("You must specify at least one constraint.")
        return cleaned_data
    
    def build_queryset(self):
        qs = Course.objects.all()
        if self.cleaned_data.get('department'):
            qs = qs.filter(departments=self.cleaned_data['department'])
        
        if self.cleaned_data.get('only_at_least') == 'O':
            
            m = Meeting.objects.filter(monday=True)
            if self.cleaned_data.get('m', False):
                qs = qs.filter(meeting__in=m)
            else:
                qs = qs.exclude(meeting__in=m)
            
            t = Meeting.objects.filter(tuesday=True)
            if self.cleaned_data.get('t', False):
                qs = qs.filter(meeting__in=t)
            else:
                qs = qs.exclude(meeting__in=t)
            
            
            w = Meeting.objects.filter(wednesday=True)
            if self.cleaned_data.get('w', False):
                qs = qs.filter(meeting__in=w)
            else:
                qs = qs.exclude(meeting__in=w)
            
            r = Meeting.objects.filter(thursday=True)
            if self.cleaned_data.get('r', False):
                qs = qs.filter(meeting__in=r)
            else:
                qs = qs.exclude(meeting__in=r)
            
            f = Meeting.objects.filter(friday=True)
            if self.cleaned_data.get('f', False):
                qs = qs.filter(meeting__in=f)
            else:
                qs = qs.exclude(meeting__in=f)
            
            if self.cleaned_data.get('start_range'):
                qs = qs.filter(meeting__in=Meeting.objects.filter(begin__gte=self.cleaned_data['start_range']))
            if self.cleaned_data.get('end_range'):
                qs = qs.filter(meeting__in=Meeting.objects.filter(end__lte=self.cleaned_data['end_range']))
            
        elif self.cleaned_data.get('only_at_least') == 'A':
            if self.cleaned_data.get('m') == True: qs = qs.filter(meeting__monday=self.cleaned_data['m'])
            if self.cleaned_data.get('t') == True: qs = qs.filter(meeting__tuesday=self.cleaned_data['t'])
            if self.cleaned_data.get('w') == True: qs = qs.filter(meeting__wednesday=self.cleaned_data['w'])
            if self.cleaned_data.get('r') == True: qs = qs.filter(meeting__thursday=self.cleaned_data['r'])
            if self.cleaned_data.get('f') == True: qs = qs.filter(meeting__friday=self.cleaned_data['f'])
            if self.cleaned_data.get('start_range'):
                qs = qs.filter(meeting__begin__gte=self.cleaned_data['start_range'])
            if self.cleaned_data.get('end_range'):
                qs = qs.filter(meeting__end__lte=self.cleaned_data['end_range'])
            
        
        campus_ids = []
        if self.cleaned_data.get('c_cgu'): campus_ids.append(CAMPUSES_LOOKUP['CGU'])
        if self.cleaned_data.get('c_cm'): campus_ids.append(CAMPUSES_LOOKUP['CM'])
        if self.cleaned_data.get('c_cu'): campus_ids.append(CAMPUSES_LOOKUP['CU'])
        if self.cleaned_data.get('c_hm'): campus_ids.append(CAMPUSES_LOOKUP['HM'])
        if self.cleaned_data.get('c_po'): campus_ids.append(CAMPUSES_LOOKUP['PO'])
        if self.cleaned_data.get('c_pz'): campus_ids.append(CAMPUSES_LOOKUP['PZ'])
        if self.cleaned_data.get('c_sc'): campus_ids.append(CAMPUSES_LOOKUP['SC'])
        
        if campus_ids:
            qs = qs.filter(meeting__campus__in=campus_ids)
        
        if self.cleaned_data.get('instructor'):
            qs = qs.filter(instructor__icontains=self.cleaned_data['instructor'])
        if self.cleaned_data.get('credit'):
            if self.cleaned_data['credit'] == 'A':
                pass
            elif self.cleaned_data['credit'] == 'F':
                qs = qs.filter(credit__gte=1.0)
            elif self.cleaned_data['credit'] == 'P':
                qs = qs.filter(credit__lt=1.0, credit__gt=0.0)
            else:
                qs = qs.filter(credit=self.cleaned_data['credit'])
        if self.cleaned_data.get('min_class_size') > 0:
            qs = qs.filter(spots__gte=self.cleaned_data['min_class_size'])
        
        if self.cleaned_data.get('keywords'):
            keywords = [a.lower() for a in keyword_regex.findall(self.cleaned_data['keywords'])]
            qs_descfilter = qs
            qs_namefilter = qs
            for kw in keywords:
                qs_descfilter = qs_descfilter.filter(description__icontains=kw)
                qs_namefilter = qs_namefilter.filter(name__icontains=kw)
            qs = (qs_descfilter or qs_namefilter)
            qs = qs.distinct()
        #if self.cleaned_data.get('course_name'):
        #    qs = qs.filter(name__icontains=self.cleaned_data['course_name'])
        
        
        qs = qs.distinct().order_by('code')
        return qs

class ScheduleForm(forms.Form):
    key = forms.CharField(max_length=100)