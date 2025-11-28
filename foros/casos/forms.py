from django import forms


class ExpedienteUploadForm(forms.Form):
    archivo_csv = forms.FileField(
        label="Archivo CSV de Expedientes",
        help_text="Seleccione el archivo expedientes_completos.csv",
    )


class MovimientoUploadForm(forms.Form):
    archivo_csv = forms.FileField(
        label="Archivo CSV de Movimientos",
        help_text="Seleccione el archivo CSV correspondiente a este expediente.",
        widget=forms.FileInput(attrs={"accept": ".csv"}),
    )
