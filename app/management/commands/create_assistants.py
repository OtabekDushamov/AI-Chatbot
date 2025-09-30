from django.core.management.base import BaseCommand
from django.conf import settings
from openai import OpenAI
from app.models import Assistant
from app.modes import MODES


class Command(BaseCommand):
    help = 'Create OpenAI assistants for each mode and store them in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of assistants even if they already exist',
        )

    def handle(self, *args, **options):
        if not settings.OPENAI_API_KEY:
            self.stdout.write(
                self.style.ERROR('OPENAI_API_KEY not found in environment variables')
            )
            return

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        force = options['force']
        
        created_count = 0
        updated_count = 0
        skipped_count = 0

        for mode_key, mode_data in MODES.items():
            self.stdout.write(f'\nProcessing mode: {mode_data["name"]}')
            
            for assistant_data in mode_data['assistants']:
                assistant_id = assistant_data['id']
                name = assistant_data['name']
                description = assistant_data['description']
                system_prompt = assistant_data['system_prompt']
                
                # Check if assistant already exists in database
                db_assistant, created = Assistant.objects.get_or_create(
                    mode_id=assistant_id,
                    defaults={
                        'name': name,
                        'description': description,
                        'system_prompt': system_prompt,
                        'mode': mode_key,
                        'assistant_id': '',  # Will be updated after OpenAI creation
                    }
                )
                
                if created:
                    self.stdout.write(f'  Created database record for: {name}')
                elif force:
                    # Update existing record
                    db_assistant.name = name
                    db_assistant.description = description
                    db_assistant.system_prompt = system_prompt
                    db_assistant.mode = mode_key
                    db_assistant.save()
                    self.stdout.write(f'  Updated database record for: {name}')
                else:
                    self.stdout.write(f'  Database record already exists for: {name}')
                
                # Create or update OpenAI assistant
                try:
                    if force or not db_assistant.assistant_id:
                        # Create new OpenAI assistant
                        openai_assistant = client.beta.assistants.create(
                            name=name,
                            description=description,
                            instructions=system_prompt,
                            model=settings.OPENAI_ASSISTANT_MODEL,
                            tools=[{"type": "code_interpreter"}]
                        )
                        
                        # Update database with OpenAI assistant ID
                        db_assistant.assistant_id = openai_assistant.id
                        db_assistant.save()
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ Created OpenAI assistant: {name} (ID: {openai_assistant.id})')
                        )
                    else:
                        # Assistant already exists in OpenAI
                        skipped_count += 1
                        self.stdout.write(f'  - Skipped: {name} (already exists)')
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Failed to create assistant {name}: {str(e)}')
                    )

        self.stdout.write(f'\n{self.style.SUCCESS("Summary:")}')
        self.stdout.write(f'  Created: {created_count}')
        self.stdout.write(f'  Updated: {updated_count}')
        self.stdout.write(f'  Skipped: {skipped_count}')
        
        if created_count > 0 or updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS('\n✓ Assistants created successfully!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('\n- No new assistants were created.')
            )
