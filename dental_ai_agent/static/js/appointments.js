let currentPage = 1;
let totalPages = 1;
let debounceTimer = null;

document.addEventListener('DOMContentLoaded', function() {
    loadDoctors();
    loadStats();
    loadAppointments();

    document.getElementById('search-input').addEventListener('input', function() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => { currentPage = 1; loadAppointments(); }, 400);
    });

    document.getElementById('doctor-filter').addEventListener('change', function() {
        currentPage = 1;
        loadAppointments();
    });

    document.getElementById('status-filter').addEventListener('change', function() {
        currentPage = 1;
        loadAppointments();
    });

    document.getElementById('date-from').addEventListener('change', function() {
        currentPage = 1;
        loadAppointments();
    });

    document.getElementById('date-to').addEventListener('change', function() {
        currentPage = 1;
        loadAppointments();
    });
});

function refreshData() {
    loadStats();
    loadAppointments();
}

function loadDoctors() {
    fetch('/api/doctors')
        .then(res => res.json())
        .then(data => {
            const select = document.getElementById('doctor-filter');
            const editSelect = document.getElementById('edit-doctor');
            data.data.forEach(doc => {
                select.innerHTML += `<option value="${doc}">${doc}</option>`;
                editSelect.innerHTML += `<option value="${doc}">${doc}</option>`;
            });
        });
}

function loadStats() {
    fetch('/api/appointments/stats')
        .then(res => res.json())
        .then(data => {
            document.getElementById('stat-total').textContent = data.total;
            document.getElementById('stat-today').textContent = data.today;
            document.getElementById('stat-pending').textContent = data.pending;
            document.getElementById('stat-completed').textContent = data.completed;
        });
}

function loadAppointments() {
    const search = document.getElementById('search-input').value;
    const doctor = document.getElementById('doctor-filter').value;
    const status = document.getElementById('status-filter').value;
    const dateFrom = document.getElementById('date-from').value;
    const dateTo = document.getElementById('date-to').value;

    let url = `/api/appointments?page=${currentPage}&limit=10&sort=desc`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (doctor) url += `&doctor=${encodeURIComponent(doctor)}`;
    if (status) url += `&status=${encodeURIComponent(status)}`;
    if (dateFrom) url += `&date_from=${dateFrom}`;
    if (dateTo) url += `&date_to=${dateTo}`;

    fetch(url)
        .then(res => res.json())
        .then(data => {
            totalPages = data.total_pages;
            renderTable(data.data);
            renderPagination(data.page, data.total_pages, data.total);
            document.getElementById('pagination-info').textContent =
                `Showing page ${data.page} of ${data.total_pages} (${data.total} total)`;
        });
}

function renderTable(appointments) {
    const tbody = document.getElementById('appointments-table-body');

    if (!appointments.length) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center text-secondary py-4">
            <i class="bi bi-inbox me-2"></i>No appointments found
        </td></tr>`;
        return;
    }

    tbody.innerHTML = appointments.map(a => `
        <tr>
            <td class="fw-bold text-secondary small">#${a.id}</td>
            <td><span class="fw-medium">${escapeHtml(a.patient_name || '-')}</span></td>
            <td class="small text-truncate" style="max-width: 120px;">${escapeHtml(a.reason || '-')}</td>
            <td class="small">${escapeHtml(a.doctor_name || '-')}</td>
            <td class="small">${a.appointment_date || '-'}</td>
            <td class="small">${a.appointment_time || '-'}</td>
            <td>${statusBadge(a.status)}</td>
            <td class="text-center">
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary" title="View" onclick="viewAppointment(${a.id})">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="btn btn-outline-warning" title="Edit" onclick="editAppointment(${a.id})">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-outline-danger" title="Delete" onclick="deleteAppointment(${a.id})">
                        <i class="bi bi-trash"></i>
                    </button>
                    ${a.status !== 'completed' ? `
                    <button class="btn btn-outline-success" title="Mark Completed" onclick="markCompleted(${a.id})">
                        <i class="bi bi-check-lg"></i>
                    </button>` : ''}
                </div>
            </td>
        </tr>
    `).join('');
}

function statusBadge(status) {
    const map = {
        'scheduled': 'bg-warning text-dark',
        'completed': 'bg-success',
        'cancelled': 'bg-danger',
        'rescheduled': 'bg-info text-dark'
    };
    const cls = map[status] || 'bg-secondary';
    return `<span class="badge ${cls} status-badge rounded-pill">${status || 'unknown'}</span>`;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function renderPagination(page, totalPages, total) {
    const ul = document.getElementById('pagination');
    if (totalPages <= 1) {
        ul.innerHTML = '';
        return;
    }

    let html = '';
    html += `<li class="page-item ${page === 1 ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="goToPage(${page - 1}); return false;">&laquo;</a>
    </li>`;

    const start = Math.max(1, page - 2);
    const end = Math.min(totalPages, page + 2);

    if (start > 1) {
        html += `<li class="page-item"><a class="page-link" href="#" onclick="goToPage(1); return false;">1</a></li>`;
        if (start > 2) html += `<li class="page-item disabled"><a class="page-link">...</a></li>`;
    }

    for (let i = start; i <= end; i++) {
        html += `<li class="page-item ${i === page ? 'active' : ''}">
            <a class="page-link" href="#" onclick="goToPage(${i}); return false;">${i}</a>
        </li>`;
    }

    if (end < totalPages) {
        if (end < totalPages - 1) html += `<li class="page-item disabled"><a class="page-link">...</a></li>`;
        html += `<li class="page-item"><a class="page-link" href="#" onclick="goToPage(${totalPages}); return false;">${totalPages}</a></li>`;
    }

    html += `<li class="page-item ${page === totalPages ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="goToPage(${page + 1}); return false;">&raquo;</a>
    </li>`;

    ul.innerHTML = html;
}

function goToPage(page) {
    currentPage = page;
    loadAppointments();
}

function viewAppointment(id) {
    fetch(`/api/appointments?page=1&limit=1&search=${id}`)
        .then(res => res.json())
        .then(data => {
            const a = data.data[0];
            if (!a) return;
            document.getElementById('view-details').innerHTML = `
                <div class="row g-3">
                    <div class="col-6"><small class="text-secondary">Appointment ID</small><p class="fw-bold mb-0">#${a.id}</p></div>
                    <div class="col-6"><small class="text-secondary">Status</small><p class="mb-0">${statusBadge(a.status)}</p></div>
                    <div class="col-6"><small class="text-secondary">Patient Name</small><p class="fw-bold mb-0">${escapeHtml(a.patient_name)}</p></div>
                    <div class="col-12"><small class="text-secondary">Address</small><p class="mb-0">${escapeHtml(a.address || '-')}</p></div>
                    <div class="col-12"><small class="text-secondary">Reason</small><p class="mb-0">${escapeHtml(a.reason || '-')}</p></div>
                    <div class="col-6"><small class="text-secondary">Doctor</small><p class="fw-bold mb-0">${escapeHtml(a.doctor_name)}</p></div>
                    <div class="col-3"><small class="text-secondary">Date</small><p class="fw-bold mb-0">${a.appointment_date}</p></div>
                    <div class="col-3"><small class="text-secondary">Time</small><p class="fw-bold mb-0">${a.appointment_time}</p></div>
                </div>
            `;
            new bootstrap.Modal(document.getElementById('viewModal')).show();
        });
}

function editAppointment(id) {
    fetch(`/api/appointments?page=1&limit=1&search=${id}`)
        .then(res => res.json())
        .then(data => {
            const a = data.data[0];
            if (!a) return;
            document.getElementById('edit-id').value = a.id;
            document.getElementById('edit-name').value = a.patient_name || '';
            document.getElementById('edit-doctor').value = a.doctor_name || '';
            document.getElementById('edit-date').value = a.appointment_date || '';
            let timeVal = '';
            if (a.appointment_time) {
                try {
                    const [t, pmam] = a.appointment_time.split(' ');
                    let [h, m] = t.split(':');
                    if (pmam === 'PM' && h !== '12') h = parseInt(h) + 12;
                    if (pmam === 'AM' && h === '12') h = '00';
                    timeVal = `${String(h).padStart(2, '0')}:${m}`;
                } catch(e) { timeVal = ''; }
            }
            document.getElementById('edit-time').value = timeVal;
            document.getElementById('edit-status').value = a.status || 'scheduled';
            new bootstrap.Modal(document.getElementById('editModal')).show();
        });
}

function saveEdit() {
    const id = document.getElementById('edit-id').value;
    const timeInput = document.getElementById('edit-time').value;
    let formattedTime = timeInput;
    if (timeInput) {
        const [h, m] = timeInput.split(':');
        const hour = parseInt(h);
        const ampm = hour >= 12 ? 'PM' : 'AM';
        const hour12 = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour;
        formattedTime = `${String(hour12).padStart(2, '0')}:${m} ${ampm}`;
    }

    const data = {
        patient_name: document.getElementById('edit-name').value,
        doctor_name: document.getElementById('edit-doctor').value,
        appointment_date: document.getElementById('edit-date').value,
        appointment_time: formattedTime,
        status: document.getElementById('edit-status').value
    };

    fetch(`/api/appointments/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(() => {
        bootstrap.Modal.getInstance(document.getElementById('editModal')).hide();
        loadStats();
        loadAppointments();
    });
}

function markCompleted(id) {
    if (!confirm('Mark this appointment as completed?')) return;
    fetch(`/api/appointments/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'completed' })
    })
    .then(res => res.json())
    .then(() => {
        loadStats();
        loadAppointments();
    });
}

function deleteAppointment(id) {
    if (!confirm('Are you sure you want to delete this appointment?')) return;
    fetch(`/api/appointments/${id}`, { method: 'DELETE' })
    .then(res => res.json())
    .then(() => {
        loadStats();
        loadAppointments();
    });
}
