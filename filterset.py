from django import forms
from django.db import models
from django.db.models import Q
from django.utils.text import capfirst

from django_qfilters.filters import Filter, CharFilter, BooleanFilter, \
    ChoiceFilter, DateFilter, DateTimeFilter, TimeFilter, ModelChoiceFilter, \
    ModelMultipleChoiceFilter, NumberFilter
from django_filters import filterset as filterset_base

FILTER_FOR_DBFIELD_DEFAULTS = {
    models.CharField: {
        'filter_class': CharFilter
    },
    models.TextField: {
        'filter_class': CharFilter
    },
    models.BooleanField: {
        'filter_class': BooleanFilter
    },
    models.DateField: {
        'filter_class': DateFilter
    },
    models.DateTimeField: {
        'filter_class': DateTimeFilter
    },
    models.TimeField: {
        'filter_class': TimeFilter
    },
    models.OneToOneField: {
        'filter_class': ModelChoiceFilter,
        'extra': lambda f: {
            'queryset': f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to),
            'to_field_name': f.rel.field_name,
        }
    },
    models.ForeignKey: {
        'filter_class': ModelChoiceFilter,
        'extra': lambda f: {
            'queryset': f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to),
            'to_field_name': f.rel.field_name
        }
    },
    models.ManyToManyField: {
        'filter_class': ModelMultipleChoiceFilter,
        'extra': lambda f: {
            'queryset': f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to),
        }
    },
    models.DecimalField: {
        'filter_class': NumberFilter,
    },
    models.SmallIntegerField: {
        'filter_class': NumberFilter,
    },
    models.IntegerField: {
        'filter_class': NumberFilter,
    },
    models.PositiveIntegerField: {
        'filter_class': NumberFilter,
    },
    models.PositiveSmallIntegerField: {
        'filter_class': NumberFilter,
    },
    models.FloatField: {
        'filter_class': NumberFilter,
    },
    models.NullBooleanField: {
        'filter_class': BooleanFilter,
    },
    models.SlugField: {
        'filter_class': CharFilter,
    },
    models.EmailField: {
        'filter_class': CharFilter,
    },
    models.FilePathField: {
        'filter_class': CharFilter,
    },
    models.URLField: {
        'filter_class': CharFilter,
    },
    models.XMLField: {
        'filter_class': CharFilter,
    },
    models.IPAddressField: {
        'filter_class': CharFilter,
    },
    models.CommaSeparatedIntegerField: {
        'filter_class': CharFilter,
    },
}

class FilterSet(filterset_base.FilterSet):
	@property
	def qs(self):
		if not hasattr(self, '_qs'):
			q_base = Q()
			qs = self.queryset.all()
			for name, filter_ in self.filters.iteritems():
				try:
					if self.is_bound:
						data = self.form[name].data
					else:
						data = self.form.initial.get(name, self.form[name].field.initial)

					val = self.form.fields[name].clean(data)

					if val or val is False or val is 0: # Stop passing it when there's no goddamn val!
						result = filter_.filter(val)
						if result:
							q_base &= result # Stop passing it the qs!!
				except forms.ValidationError:
					pass
			self._qs = qs.filter(q_base).distinct()

		return self._qs

	@classmethod
	def filter_for_field(cls, f, name):
		filter_for_field = dict(FILTER_FOR_DBFIELD_DEFAULTS, **cls.filter_overrides)

		default = {
			'name': name,
			'label': capfirst(f.verbose_name)
		}

		data = filter_for_field.get(f.__class__)
		filter_class = data.get('filter_class')
		if f.choices:
			default['choices'] = f.choices
			if filter_class == CharFilter:
				filter_class = ChoiceFilter
			#return ChoiceFilter(**default)

		if data is None:
			return

		default.update(data.get('extra', lambda f: {})(f))
		if filter_class is not None:
			return filter_class(**default)

