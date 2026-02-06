from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import PrayerEntry, Tag
from extensions import db
from utils import extract_tags

guide_bp = Blueprint('guide', __name__, url_prefix='/guide')

@guide_bp.route('/')
@login_required
def acts_wizard():
    return render_template('prayer_guide.html') # Use the better template

@guide_bp.route('/submit', methods=['POST'])
@login_required
def submit_acts():
    adoration = request.form.get('adoration', '')
    confession = request.form.get('confession', '')
    thanksgiving = request.form.get('thanksgiving', '')
    supplication = request.form.get('supplication', '')

    # Protestant-friendly formatting
    content = "My Prayer Journey:\n\n"
    if adoration: content += f"🙌 Praise: {adoration}\n"
    if confession: content += f"🛐 Repentance: {confession}\n"
    if thanksgiving: content += f"🙏 Gratitude: {thanksgiving}\n"
    if supplication: content += f"🤲 Requests: {supplication}\n"

    entry = PrayerEntry(user_id=current_user.id, content=content)

    # Auto-tag
    tag_names = extract_tags(content)
    if "ACTS" not in tag_names:
        tag_names.append("ACTS")

    for name in tag_names:
        tag = Tag.query.filter_by(name=name).first()
        if not tag:
            tag = Tag(name=name, count=1)
            db.session.add(tag)
        else:
            tag.count += 1
        entry.tags.append(tag)

    db.session.add(entry)
    db.session.commit()

    flash('Guided prayer saved to your diary.')
    return redirect(url_for('entry.user_dashboard'))
