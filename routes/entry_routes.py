from flask import Blueprint, render_template, redirect, url_for, flash, request, make_response, session
from flask_login import login_required, current_user
from models import PrayerEntry, Tag, entry_tags, CommunityEmail, BlockedUser, PrayerList, PrayerListItem
from extensions import db
from utils import extract_tags, get_geolocation, ProfanityFilter
from utils.gamification import check_and_award_badges
from flask_babel import _
import json
from datetime import datetime, timedelta
from sqlalchemy import func
import csv
import io
from fpdf import FPDF
from flask import Response
import calendar

entry_bp = Blueprint('entry', __name__)

@entry_bp.route('/calendar')
@login_required
def calendar_view():
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)

    # Adjust month if out of range
    if month > 12: month, year = 1, year + 1
    if month < 1: month, year = 12, year - 1

    cal = calendar.Calendar(firstweekday=6) # Sunday start
    month_days = cal.monthdatescalendar(year, month)

    # Fetch entries for this month range
    start_date = month_days[0][0]
    end_date = month_days[-1][-1]

    entries = PrayerEntry.query.filter(
        PrayerEntry.user_id == current_user.id,
        func.date(PrayerEntry.created_at) >= start_date,
        func.date(PrayerEntry.created_at) <= end_date
    ).all()

    # Map dates to entry counts/statuses
    # Using a dict: {date_obj: [entries]}
    date_map = {}
    for e in entries:
        d = e.created_at.date()
        if d not in date_map: date_map[d] = []
        date_map[d].append(e)

    # Month name
    month_name = calendar.month_name[month]

    return render_template('calendar.html',
                           month_days=month_days,
                           date_map=date_map,
                           year=year,
                           month=month,
                           month_name=month_name)

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

    # Memories: On This Day
    today = datetime.now()
    memories = PrayerEntry.query.filter(
        PrayerEntry.user_id == current_user.id,
        func.extract('month', PrayerEntry.created_at) == today.month,
        func.extract('day', PrayerEntry.created_at) == today.day,
        func.extract('year', PrayerEntry.created_at) < today.year
    ).order_by(PrayerEntry.created_at.desc()).all()

    return render_template('user_dashboard.html', entries=entries, memories=memories)

@entry_bp.route('/add', methods=['POST'])
@login_required
def add_entry():
    content = request.form.get('content')
    is_public = 'is_public' in request.form
    is_anonymous = 'is_anonymous' in request.form
    is_private = 'is_private' in request.form
    is_urgent = 'is_urgent' in request.form
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
        is_urgent = False # Urgent implies public visibility usually

    if is_urgent:
        is_public = True # Urgent must be public to be seen

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
        is_urgent=is_urgent,
        urgent_expiry=datetime.utcnow() + timedelta(hours=24) if is_urgent else None,
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

@entry_bp.route('/export/json')
@login_required
def export_json():
    entries = PrayerEntry.query.filter_by(user_id=current_user.id).order_by(PrayerEntry.created_at.desc()).all()

    data = []
    for entry in entries:
        data.append({
            'id': entry.id,
            'content': entry.content,
            'created_at': entry.created_at.isoformat(),
            'status': entry.status,
            'tags': [t.name for t in entry.tags],
            'category': entry.category,
            'is_private': entry.is_private,
            'is_public': entry.is_public,
            'reflection': entry.reflection,
            'mood': entry.mood
        })

    response = make_response(json.dumps(data, indent=4))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = 'attachment; filename=prayer_diary.json'
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

@entry_bp.route('/lists')
@login_required
def prayer_lists():
    lists = PrayerList.query.filter_by(user_id=current_user.id).all()
    return render_template('prayer_lists.html', lists=lists)

@entry_bp.route('/lists/create', methods=['POST'])
@login_required
def create_list():
    name = request.form.get('name')
    if name:
        new_list = PrayerList(user_id=current_user.id, name=name)
        db.session.add(new_list)
        db.session.commit()
        flash(_('Prayer list created.'))
    return redirect(url_for('entry.prayer_lists'))

@entry_bp.route('/lists/<int:list_id>/delete', methods=['POST'])
@login_required
def delete_list(list_id):
    plist = PrayerList.query.get_or_404(list_id)
    if plist.user_id != current_user.id:
        flash(_('Unauthorized'))
        return redirect(url_for('entry.prayer_lists'))

    db.session.delete(plist)
    db.session.commit()
    flash(_('Prayer list deleted.'))
    return redirect(url_for('entry.prayer_lists'))

@entry_bp.route('/lists/<int:list_id>/item', methods=['POST'])
@login_required
def add_list_item(list_id):
    plist = PrayerList.query.get_or_404(list_id)
    if plist.user_id != current_user.id:
        flash(_('Unauthorized'))
        return redirect(url_for('entry.prayer_lists'))

    content = request.form.get('content')
    if content:
        item = PrayerListItem(list_id=plist.id, content=content)
        db.session.add(item)
        db.session.commit()

    return redirect(url_for('entry.prayer_lists'))

@entry_bp.route('/lists/item/<int:item_id>/toggle', methods=['POST'])
@login_required
def toggle_list_item(item_id):
    item = PrayerListItem.query.get_or_404(item_id)
    if item.list.user_id != current_user.id:
        flash(_('Unauthorized'))
        return redirect(url_for('entry.prayer_lists'))

    item.is_answered = not item.is_answered
    db.session.commit()
    return redirect(url_for('entry.prayer_lists'))

@entry_bp.route('/lists/item/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_list_item(item_id):
    item = PrayerListItem.query.get_or_404(item_id)
    if item.list.user_id != current_user.id:
        flash(_('Unauthorized'))
        return redirect(url_for('entry.prayer_lists'))

    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('entry.prayer_lists'))

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
