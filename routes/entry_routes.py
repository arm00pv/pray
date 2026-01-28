from flask import Blueprint, render_template, redirect, url_for, flash, request, make_response, session
from flask_login import login_required, current_user
from models import PrayerEntry, Tag, entry_tags, CommunityEmail, BlockedUser
from extensions import db
from utils import extract_tags, get_geolocation, ProfanityFilter
from utils.gamification import check_and_award_badges
from flask_babel import _
import json
from datetime import datetime
import csv
import io
from fpdf import FPDF
from flask import Response

entry_bp = Blueprint('entry', __name__)

@entry_bp.route('/dashboard')
@login_required
def user_dashboard():
    if current_user.get_id().startswith('admin_'):
        return redirect(url_for('admin.dashboard'))

    query = PrayerEntry.query.filter_by(user_id=current_user.id)

    # Search & Filtering
    q = request.args.get('q')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    tag_filter = request.args.get('tag')

    if q:
        query = query.filter(PrayerEntry.content.ilike(f'%{q}%'))

    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(PrayerEntry.created_at >= start_dt)
        except ValueError:
            pass

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            # Add one day to include the end date fully (since time is 00:00:00)
            # Or just ignore time if SQLite handling allows
            query = query.filter(PrayerEntry.created_at <= end_dt)
        except ValueError:
            pass

    if tag_filter:
        query = query.join(PrayerEntry.tags).filter(Tag.name == tag_filter)

    entries = query.order_by(PrayerEntry.created_at.desc()).all()

    return render_template('user_dashboard.html', entries=entries)

@entry_bp.route('/add', methods=['POST'])
@login_required
def add_entry():
    content = request.form.get('content')
    is_public = 'is_public' in request.form
    is_anonymous = 'is_anonymous' in request.form
    is_private = 'is_private' in request.form
    category = request.form.get('category')

    if not content:
        flash('Prayer content cannot be empty.')
        return redirect(url_for('entry.user_dashboard'))

    # Check if user is blocked
    blocked = BlockedUser.query.filter((BlockedUser.user_id == current_user.id) | (BlockedUser.email == current_user.email)).first()
    if blocked:
        flash('Your account is blocked from posting.')
        return redirect(url_for('entry.user_dashboard'))

    # Enforce privacy logic: If private, it cannot be public
    if is_private:
        is_public = False

    pf = ProfanityFilter()
    if pf.is_profane(content):
        flash('Content contains profanity and cannot be posted.')
        return redirect(url_for('entry.user_dashboard'))

    # IP and Geo
    ip = request.remote_addr
    # On some proxies/hosting, use X-Forwarded-For
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0]

    geo_data = get_geolocation(ip)

    entry = PrayerEntry(
        user_id=current_user.id,
        content=content,
        ip_address=ip,
        geolocation_data=json.dumps(geo_data) if geo_data else None,
        is_public=is_public,
        is_anonymous=is_anonymous,
        is_private=is_private,
        category=category
    )

    # Tags
    locale = session.get('language', request.accept_languages.best_match(['en', 'es']))
    tag_names = extract_tags(content, locale=locale)
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

    # Check badges
    new_badges = check_and_award_badges(current_user)
    if new_badges:
        names = ", ".join([b.name for b in new_badges])
        flash(_('Prayer entry added. You earned new badges: %(names)s!', names=names))
    else:
        flash(_('Prayer entry added.'))

    return redirect(url_for('entry.user_dashboard'))

@entry_bp.route('/add_anonymous', methods=['POST'])
def add_anonymous_entry():
    content = request.form.get('content')
    email = request.form.get('email')
    agreed = request.form.get('agreed_to_terms')

    if not content or not email or not agreed:
        flash('All fields including agreement to terms are required for anonymous posting.')
        return redirect(url_for('index'))

    # Check if email is blocked
    blocked = BlockedUser.query.filter_by(email=email).first()
    if blocked:
        flash('This email address is blocked from posting.')
        return redirect(url_for('index'))

    pf = ProfanityFilter()
    if pf.is_profane(content):
        flash('Content contains profanity and cannot be posted.')
        return redirect(url_for('index'))

    # IP and Geo
    ip = request.remote_addr
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0]

    geo_data = get_geolocation(ip)

    # Handle Email Record
    comm_email = CommunityEmail.query.filter_by(email=email).first()
    if not comm_email:
        comm_email = CommunityEmail(email=email, agreed_to_terms=True)
        db.session.add(comm_email)
        db.session.commit() # Commit to get ID

    entry = PrayerEntry(
        user_id=None,
        community_email_id=comm_email.id,
        content=content,
        ip_address=ip,
        geolocation_data=json.dumps(geo_data) if geo_data else None,
        is_public=True,
        is_anonymous=True,
        is_private=False
    )

    # Tags
    locale = session.get('language', request.accept_languages.best_match(['en', 'es']))
    tag_names = extract_tags(content, locale=locale)
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
    flash('Anonymous prayer shared successfully.')
    return redirect(url_for('index'))

@entry_bp.route('/entry/<int:entry_id>/status', methods=['POST'])
@login_required
def update_status(entry_id):
    entry = PrayerEntry.query.get_or_404(entry_id)
    if entry.user_id != current_user.id:
        flash('Unauthorized')
        return redirect(url_for('entry.user_dashboard'))

    status = request.form.get('status')
    if status in ['active', 'fulfilled', 'dropped']:
        entry.status = status
        db.session.commit()

    return redirect(url_for('entry.user_dashboard'))

@entry_bp.route('/export/csv')
@login_required
def export_csv():
    entries = PrayerEntry.query.filter_by(user_id=current_user.id).order_by(PrayerEntry.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Content', 'Status', 'Tags'])

    for entry in entries:
        tags = ", ".join([t.name for t in entry.tags])
        writer.writerow([entry.created_at.strftime('%Y-%m-%d %H:%M'), entry.content, entry.status, tags])

    output.seek(0)

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=prayer_diary.csv"}
    )

@entry_bp.route('/export/pdf')
@login_required
def export_pdf():
    entries = PrayerEntry.query.filter_by(user_id=current_user.id).order_by(PrayerEntry.created_at.desc()).all()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="My Prayer Diary", ln=1, align="C")
    pdf.ln(10)

    for entry in entries:
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 10, txt=f"Date: {entry.created_at.strftime('%Y-%m-%d %H:%M')} | Status: {entry.status}", ln=1)
        pdf.set_font("Arial", size=10)
        # MultiCell for content to wrap text
        pdf.multi_cell(0, 10, txt=f"Content: {entry.content}")
        tags = ", ".join([t.name for t in entry.tags])
        pdf.cell(0, 10, txt=f"Tags: {tags}", ln=1)
        pdf.ln(5)

    response = make_response(pdf.output(dest='S').encode('latin-1'))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=prayer_diary.pdf'
    return response

@entry_bp.route('/entry/<int:entry_id>/continuous', methods=['POST'])
@login_required
def toggle_continuous(entry_id):
    entry = PrayerEntry.query.get_or_404(entry_id)
    if entry.user_id != current_user.id:
        flash('Unauthorized')
        return redirect(url_for('entry.user_dashboard'))

    entry.is_continuous = not entry.is_continuous
    db.session.commit()
    return redirect(url_for('entry.user_dashboard'))

@entry_bp.route('/entry/<int:entry_id>/sticker', methods=['POST'])
@login_required
def add_sticker(entry_id):
    entry = PrayerEntry.query.get_or_404(entry_id)
    if entry.user_id != current_user.id:
        flash('Unauthorized')
        return redirect(url_for('entry.user_dashboard'))

    sticker = request.form.get('sticker')
    if sticker:
        if entry.stickers:
            entry.stickers += f",{sticker}"
        else:
            entry.stickers = sticker
        db.session.commit()

    return redirect(url_for('entry.user_dashboard'))
@entry_bp.route('/reflection/<int:entry_id>', methods=['POST'])
@login_required
def update_reflection(entry_id):
    entry = PrayerEntry.query.get_or_404(entry_id)
    if entry.user_id != current_user.id:
        flash(_('Unauthorized action.'))
        return redirect(url_for('entry.user_dashboard'))

    reflection = request.form.get('reflection')
    entry.reflection = reflection
    db.session.commit()
    flash(_('Reflection updated.'))
    return redirect(url_for('entry.user_dashboard'))
@entry_bp.route('/guide')
@login_required
def prayer_guide():
    return render_template('prayer_guide.html')

@entry_bp.route('/guide/submit', methods=['POST'])
@login_required
def submit_guide():
    adoration = request.form.get('adoration', '')
    confession = request.form.get('confession', '')
    thanksgiving = request.form.get('thanksgiving', '')
    supplication = request.form.get('supplication', '')

    # Construct structured content
    content_parts = []
    if adoration:
        content_parts.append(f"🙌 Adoration: {adoration}")
    if confession:
        content_parts.append(f"🛐 Confession: {confession}")
    if thanksgiving:
        content_parts.append(f"🙏 Thanksgiving: {thanksgiving}")
    if supplication:
        content_parts.append(f"🤲 Supplication: {supplication}")

    full_content = "\n\n".join(content_parts)

    if not full_content:
        flash(_("Prayer guide was empty."))
        return redirect(url_for('entry.user_dashboard'))

    # Create private entry
    entry = PrayerEntry(
        user_id=current_user.id,
        content=full_content,
        is_public=False,
        is_private=True,
        category="Guided Prayer"
    )

    db.session.add(entry)
    db.session.commit()

    flash(_("Guided prayer saved to your diary."))
    return redirect(url_for('entry.user_dashboard'))

@entry_bp.route('/archive')
@login_required
def archive():
    entries = PrayerEntry.query.filter_by(user_id=current_user.id).order_by(PrayerEntry.created_at.desc()).all()

    # Structure: tree[year][month][week][day] = [entries]
    from collections import defaultdict
    # 4 levels of nesting
    tree = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))

    for entry in entries:
        year = entry.created_at.year
        month = entry.created_at.strftime('%B')
        week = f"Week {entry.created_at.strftime('%V')}"
        day = entry.created_at.strftime('%d (%A)')

        tree[year][month][week][day].append(entry)

    return render_template('archive.html', tree=tree)
