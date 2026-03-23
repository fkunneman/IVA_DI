from django.core.management import BaseCommand


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('model_name')
        parser.add_argument('file')

    def handle(self, *args, **options):
        model_name = options['model_name']
        file = options['file']

        from whisper.whisper import transcribe
        print(transcribe(model_name, file))
