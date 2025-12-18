import json
from unfold.components import BaseComponent,register_component
from .utils import bar_chart_data,subcategorias_rentables

@register_component
class BarChartMetricas(BaseComponent):
    def get_context_data(self, periodo="30dias", line_type="ingresos", **kwargs):
        context = super().get_context_data(**kwargs)
        
        if periodo == "24horas":
            data,label = bar_chart_data(periodo,type=line_type,hours=24)
        elif periodo == "30dias":
            data,label = bar_chart_data(periodo,type=line_type,days=30)
        elif periodo == "1año":
            data,label = bar_chart_data(periodo,type=line_type,month=12)
        else:
            data,label = bar_chart_data(periodo,type=line_type)

        labels = list(data.keys())
        data_values = list(data.values())

        context.update({
            "height": 250,
            "data": json.dumps({
                "labels": labels, 
                "datasets": [
                    {
                        "label": label,
                        "type": "line",
                        "data": data_values, 
                        "borderColor": "var(--color-primary-400)",
                        "fill": True,
                        "backgroundColor": "rgba(59, 130, 246, 0.3)",
                        "tension": 0.4,
                    },
                ]
            }),
            "options": json.dumps({
                "responsive": True,
                "maintainAspectRatio": False, 
                
                "animation": {
                    "duration": 1500,
                    "easing": "easeOutQuart"
                },
                "plugins": {
                    "legend": {
                        "display": False
                    }
                },
                "scales": {
                    "y": {
                        "beginAtZero": True
                    }
                }
            })
        })
        return context

@register_component
class PieChartCategorias(BaseComponent):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        labels = []
        data_values = []

        categorias = subcategorias_rentables()

        if categorias:
            for cat in categorias:
                labels.append(cat['subcategoria_nombre'])
                data_values.append(float(cat['total_vendido']))

        context.update({
            "height": 220,
            "data": json.dumps({
                "labels": labels,
                "datasets": [
                    {
                        "data": data_values,
                        "backgroundColor": [
                            "var(--color-primary-300)",
                            "var(--color-primary-500)",
                            "var(--color-primary-700)",
                            "var(--color-primary-900)",
                            "var(--color-primary-200)"
                        ],
                        "borderWidth": 1,
                        "type": "doughnut",
                        "label": "Total Vendido",
                        "hoverOffset": 4,
                    }
                ],
            }),
            "options": json.dumps({
                "animation": {
                    "duration": 2000,
                    "animateRotate": True,
                    "animateScale": False
                },
                "plugins": {
                    "legend": {
                        "display": True,
                        "position": "bottom",
                        "align": "center",
                        "labels": {
                            "font": {
                                "size": 14
                            },
                            "padding": 20,
                            "usePointStyle": True,
                        }
                    }
                },
            })
        })
        return context