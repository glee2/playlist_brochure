import pygal

class LineChart():
    def __init__(self, **kwargs):
        self.chart = pygal.Line(**kwargs)

    def generate(self, data):
        for key, value in data.items():
            self.chart.add(key, value)

        return self.chart.render(is_unicode=True)

class GaugeChart():
    def __init__(self, **kwargs):
        self.gauge = pygal.SolidGauge(**kwargs)

    def generate(self, data):
        percent_formatter = lambda x: '{:.3g}%'.format(x)
        self.gauge.value_formatter = percent_formatter

        for key, value in data.items():
            self.gauge.add(key, value)

        return self.gauge.render(is_unicode=True)
