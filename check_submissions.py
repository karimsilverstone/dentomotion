#!/usr/bin/env python
"""
Debug script to check submission files
Run: docker-compose exec web python check_submissions.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.homework.models import Submission

print("=" * 60)
print("CHECKING HOMEWORK SUBMISSIONS")
print("=" * 60)

# Get all submissions
all_subs = Submission.objects.all()
total = all_subs.count()

print(f"\n📊 Total submissions: {total}")

# Count with and without files
with_files = Submission.objects.exclude(file='').exclude(file__isnull=True).count()
without_files = total - with_files

print(f"✅ With files: {with_files}")
print(f"❌ Without files: {without_files}")

# Show first 5 submissions
print("\n📋 Sample submissions:")
print("-" * 60)

for sub in all_subs[:5]:
    print(f"\nID: {sub.id}")
    print(f"Student: {sub.student.get_full_name()}")
    print(f"Homework: {sub.homework.title}")
    print(f"Status: {sub.status}")
    print(f"File field: '{sub.file}'")
    print(f"File name: '{sub.file.name if sub.file else 'NULL'}'")
    
    if sub.file:
        file_path = sub.file.path
        exists = os.path.exists(file_path)
        print(f"File path: {file_path}")
        print(f"File exists on disk: {exists}")
        if exists:
            file_size = os.path.getsize(file_path)
            print(f"File size: {file_size} bytes ({file_size / 1024:.2f} KB)")
    else:
        print(f"❌ NO FILE ATTACHED")

print("\n" + "=" * 60)

# Check submissions without files
if without_files > 0:
    print(f"\n⚠️ Found {without_files} submissions without files:")
    print("-" * 60)
    
    for sub in Submission.objects.filter(file='')[:10]:
        print(f"- ID {sub.id}: {sub.student.get_full_name()} → {sub.homework.title} (Status: {sub.status})")

print("\n✅ Check complete!")
print("\nIf files are NULL:")
print("1. Files were never uploaded (frontend issue)")
print("2. Student needs to resubmit with the fixed API")
print("3. Check frontend is using FormData, not JSON")

