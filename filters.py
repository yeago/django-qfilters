from datetime import datetime, timedelta

from django import forms
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from django_filters.fields import RangeField, LookupTypeField

__all__ = [
    'Filter', 'CharFilter', 'BooleanFilter', 'ChoiceFilter',
    'MultipleChoiceFilter', 'DateFilter', 'DateTimeFilter', 'TimeFilter',
    'ModelChoiceFilter', 'ModelMultipleChoiceFilter', 'NumberFilter',
    'RangeFilter', 'DateRangeFilter', 'AllValuesFilter',
]

from django_filters import filters

class Filter(filters.Filter):
    def filter(self, value):
        if isinstance(value, (list, tuple)):
            lookup = str(value[1])
            if not lookup:
                lookup = 'exact' # we fallback to exact if no choice for lookup is provided
            value = value[0]
            if not value:
                return
        else:
            lookup = self.lookup_type
        return Q(**{'%s__%s' % (self.name, lookup): value})

class CharFilter(Filter):
    field_class = forms.CharField

class BooleanFilter(Filter):
    field_class = forms.NullBooleanField

    def filter(self, value):
        return Q(**{self.name: value})

class ChoiceFilter(Filter):
    field_class = forms.ChoiceField

class MultipleChoiceFilter(Filter):
    """
    This filter preforms an OR query on the selected options.
    """
    field_class = forms.MultipleChoiceField

    def filter(self, value):
        value = value or ()
        # TODO: this is a bit of a hack, but ModelChoiceIterator doesn't have a
        # __len__ method
        if len(value) == len(list(self.field.choices)) and len(list(self.field.choices)) > 1:
            return
        
        q = Q()
        for v in value:
            q |= Q(**{self.name: v})
        return Q(q)

class DateFilter(Filter):
    field_class = forms.DateField

class DateTimeFilter(Filter):
    field_class = forms.DateTimeField

class TimeFilter(Filter):
    field_class = forms.TimeField

class ModelChoiceFilter(Filter):
    field_class = forms.ModelChoiceField

class ModelMultipleChoiceFilter(MultipleChoiceFilter):
    field_class = forms.ModelMultipleChoiceField

class NumberFilter(Filter):
    field_class = forms.DecimalField

class RangeFilter(Filter):
    field_class = RangeField

    def filter(self, value):
        if value:
            return Q(**{'%s__range' % self.name: (value.start, value.stop)})
        return qs

class DateRangeFilter(ChoiceFilter):
    options = {
        '': (_('Any Date'), lambda name: Q()),
        1: (_('Today'), lambda name: Q(**{
            '%s__year' % name: datetime.today().year,
            '%s__month' % name: datetime.today().month,
            '%s__day' % name: datetime.today().day
        })),
        2: (_('Past 7 days'), lambda name: Q(**{
            '%s__gte' % name: (datetime.today() - timedelta(days=7)).strftime('%Y-%m-%d'),
            '%s__lt' % name: (datetime.today()+timedelta(days=1)).strftime('%Y-%m-%d'),
        })),
        3: (_('This month'), lambda name: Q(**{
            '%s__year' % name: datetime.today().year,
            '%s__month' % name: datetime.today().month
        })),
        4: (_('This year'), lambda name: Q(**{
            '%s__year' % name: datetime.today().year,
        })),
    }

    def __init__(self, *args, **kwargs):
        kwargs['choices'] = [(key, value[0]) for key, value in self.options.iteritems()]
        super(DateRangeFilter, self).__init__(*args, **kwargs)

    def filter(self, value):
        try:
            value = int(value)
        except (ValueError, TypeError):
            value = ''
            
        return self.options[value][1](self.name)

class AllValuesFilter(ChoiceFilter):
    @property
    def field(self):
        qs = self.model._default_manager.distinct().order_by(self.name).values_list(self.name, flat=True)
        self.extra['choices'] = [(o, o) for o in qs]
        return super(AllValuesFilter, self).field
