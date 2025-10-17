from django.core.management.base import BaseCommand
from rifa_app.models import Numero

class Command(BaseCommand):
    help = 'Generates 10000 raffle numbers from 0000 to 9999.'

    def handle(self, *args, **options):
        self.stdout.write("Starting number generation...")

        for i in range(10000):
            numero_str = f"{i:04d}"
            Numero.objects.create(numero=numero_str)
        
        self.stdout.write(self.style.SUCCESS("Successfully generated 10000 numbers!"))