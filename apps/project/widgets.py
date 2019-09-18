from functools import reduce

from django import forms


class PermissionsWidget(forms.Widget):
    def __init__(self, name, permission_values, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.widget_name = name
        self.permission_values = permission_values

    def value_from_datadict(self, data, files, name):
        """
        Get the checkbox values and or them to get the final value
        """
        to_or_vals = [
            v if data.get(f'{self.widget_name}_{k}') == 'on' else 0
            for k, v in self.permission_values.items()
        ]
        return reduce(
            lambda acc, x: acc | x,
            to_or_vals
        )

    def render(self, name, value, attrs=None, renderer=None):
        html = ''
        for k, v in self.permission_values.items():
            checked = value & v == v
            html += f'''
                <span style="margin-right:30px">
                    <input type="checkbox" name="{self.widget_name}_{k}" {"checked" if checked else ""}/>
                    {k}
                </span>
            '''

        return html
