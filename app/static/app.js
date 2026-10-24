const apiRoot = window.location.origin;

function showSection(id) {
  document.querySelectorAll('.panel').forEach(panel => panel.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}

async function fetchJson(path, options = {}) {
  const response = await fetch(`${apiRoot}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || data.message || JSON.stringify(data));
  return data;
}

function buildTable(items, columns) {
  if (!Array.isArray(items) || items.length === 0) {
    return '<p>No records found.</p>';
  }
  const header = `<tr>${columns.map(col => `<th>${col.label}</th>`).join('')}</tr>`;
  const rows = items.map(item => `<tr>${columns.map(col => `<td>${item[col.key] ?? ''}</td>`).join('')}</tr>`).join('');
  return `<table>${header}${rows}</table>`;
}

function statusMessage(containerId, message, isError = false) {
  const el = document.getElementById(containerId);
  if (el) {
    el.textContent = message;
    el.style.color = isError ? '#b91c1c' : '#0f172a';
  }
}

function renderOperationalAlerts(alerts = []) {
  const container = document.getElementById('overview-alerts');
  container.replaceChildren();

  const heading = document.createElement('h3');
  heading.textContent = 'Operational Alerts';
  container.append(heading);

  if (!alerts.length) {
    const message = document.createElement('p');
    message.className = 'alert-empty';
    message.textContent = 'No active alerts';
    container.append(message);
    return;
  }

  const list = document.createElement('ul');
  list.className = 'alert-items';
  alerts.forEach(alert => {
    const item = document.createElement('li');
    item.className = `alert-item ${alert.level === 'critical' ? 'critical' : 'warning'}`;
    item.textContent = alert.message;
    list.append(item);
  });
  container.append(list);
}

async function loadOverview() {
  try {
    const metrics = await fetchJson('/health/metrics');
    const overview = document.getElementById('overview-metrics');
    overview.innerHTML = `
      <h3>Live Count Metrics</h3>
      <p><strong>Patients:</strong> ${metrics.metrics.total_patients}</p>
      <p><strong>Doctors:</strong> ${metrics.metrics.total_doctors}</p>
      <p><strong>Beds:</strong> ${metrics.metrics.total_beds}</p>
      <p><strong>Occupied Beds:</strong> ${metrics.metrics.occupied_beds}/50 (${metrics.metrics.bed_occupancy_rate}% )</p>
      <p><strong>Appointments:</strong> ${metrics.metrics.total_appointments}</p>
      <p><strong>Doctor Availability:</strong> ${metrics.metrics.doctor_availability_rate}%</p>
    `;
    renderOperationalAlerts(metrics.alerts);
  } catch (error) {
    document.getElementById('overview-metrics').textContent = `Unable to load metrics: ${error.message}`;
    renderOperationalAlerts();
  }

  try {
    const health = await fetchJson('/health/');
    document.getElementById('overview-status').innerHTML = `<h3>Service Status</h3><p>${health.status}</p><p>${new Date(health.timestamp).toLocaleString()}</p>`;
  } catch (error) {
    document.getElementById('overview-status').textContent = `Unable to load health: ${error.message}`;
  }
}

async function loadPatients() {
  try {
    const patients = await fetchJson('/patients');
    const columns = [
      { label: 'ID', key: 'id' },
      { label: 'Patient ID', key: 'patient_id' },
      { label: 'Department', key: 'department' },
      { label: 'Acuity', key: 'acuity_level' },
      { label: 'Arrival', key: 'arrival_time' },
    ];
    document.getElementById('patients-table').innerHTML = buildTable(patients, columns);
  } catch (error) {
    document.getElementById('patients-table').textContent = `Error loading patients: ${error.message}`;
  }
}

async function loadDoctors() {
  try {
    const doctors = await fetchJson('/doctors');
    const columns = [
      { label: 'ID', key: 'id' },
      { label: 'Doctor ID', key: 'doctor_id' },
      { label: 'Name', key: 'name' },
      { label: 'Specialty', key: 'specialty' },
      { label: 'Department', key: 'department' },
      { label: 'Available', key: 'is_available' },
    ];
    document.getElementById('doctors-table').innerHTML = buildTable(doctors, columns);
  } catch (error) {
    document.getElementById('doctors-table').textContent = `Error loading doctors: ${error.message}`;
  }
}

async function loadBeds() {
  try {
    const beds = await fetchJson('/beds');
    const columns = [
      { label: 'ID', key: 'id' },
      { label: 'Bed Number', key: 'bed_number' },
      { label: 'Department', key: 'department' },
      { label: 'Room Type', key: 'room_type' },
      { label: 'Occupied', key: 'is_occupied' },
      { label: 'Last Cleaned', key: 'last_cleaned' },
    ];
    document.getElementById('beds-table').innerHTML = buildTable(beds, columns);
  } catch (error) {
    document.getElementById('beds-table').textContent = `Error loading beds: ${error.message}`;
  }
}

async function loadAppointments() {
  try {
    const appointments = await fetchJson('/appointments');
    const columns = [
      { label: 'ID', key: 'id' },
      { label: 'Appointment ID', key: 'appointment_id' },
      { label: 'Patient ID', key: 'patient_id' },
      { label: 'Doctor ID', key: 'doctor_id' },
      { label: 'Scheduled Time', key: 'scheduled_time' },
      { label: 'Status', key: 'status' },
    ];
    document.getElementById('appointments-table').innerHTML = buildTable(appointments, columns);
  } catch (error) {
    document.getElementById('appointments-table').textContent = `Error loading appointments: ${error.message}`;
  }
}

async function loadAdminSummary() {
  try {
    const summary = await fetchJson('/admin/summary');
    document.getElementById('admin-summary').innerHTML = `
      <p><strong>Patients:</strong> ${summary.patients}</p>
      <p><strong>Doctors:</strong> ${summary.doctors}</p>
      <p><strong>Beds:</strong> ${summary.beds}</p>
      <p><strong>Appointments:</strong> ${summary.appointments}</p>
      <p><strong>Staff:</strong> ${summary.staff}</p>
    `;
  } catch (error) {
    document.getElementById('admin-summary').textContent = `Unable to load admin summary: ${error.message}`;
  }
}

async function resetData() {
  try {
    statusMessage('admin-action-status', 'Resetting data...');
    await fetchJson('/admin/reset', { method: 'POST' });
    statusMessage('admin-action-status', 'Data reset successfully');
    loadOverview();
    loadPatients();
    loadDoctors();
    loadBeds();
    loadAppointments();
    loadAdminSummary();
  } catch (error) {
    statusMessage('admin-action-status', `Reset failed: ${error.message}`, true);
  }
}

async function seedLargeDemo() {
  try {
    statusMessage('admin-action-status', 'Seeding large demo dataset...');
    const response = await fetchJson('/admin/seed', { method: 'POST' });
    statusMessage('admin-action-status', `Seed complete: ${response.message}`);
    loadOverview();
    loadPatients();
    loadDoctors();
    loadBeds();
    loadAppointments();
    loadAdminSummary();
  } catch (error) {
    statusMessage('admin-action-status', `Seed failed: ${error.message}`, true);
  }
}

async function initializeModels() {
  try {
    const response = await fetchJson('/predictive/init', { method: 'POST', body: JSON.stringify({}) });
    statusMessage('predictive-status', `Models initialized: ${response.message}`);
    await loadTrainingSummary();
  } catch (error) {
    statusMessage('predictive-status', `Model init failed: ${error.message}`, true);
  }
}

async function loadTrainingSummary() {
  const container = document.getElementById('model-training-summary');
  try {
    const summary = await fetchJson('/predictive/training-summary');
    const metrics = summary.er_wait_time_metrics;
    const score = document.createElement('p');
    score.textContent = `${metrics.target_source} labels | MAE ${metrics.mae.toFixed(1)} min | RMSE ${metrics.rmse.toFixed(1)} min`;
    const list = document.createElement('ul');
    list.className = 'feature-list';
    metrics.feature_importance.slice(0, 5).forEach(item => {
      const row = document.createElement('li');
      row.textContent = `${item.feature.replaceAll('_', ' ')}: ${(item.importance * 100).toFixed(1)}%`;
      list.append(row);
    });
    container.replaceChildren(score, list);
  } catch (error) {
    container.textContent = `Training summary unavailable: ${error.message}`;
  }
}

async function reloadPredictiveStatus() {
  try {
    const status = await fetchJson('/predictive/status');
    document.getElementById('predictive-status').textContent = `Initialized: ${status.initialized}`;
    if (status.initialized) await loadTrainingSummary();
  } catch (error) {
    statusMessage('predictive-status', `Unable to load status: ${error.message}`, true);
  }
}

async function predictERWait() {
  try {
    const payload = {
      patient_id: null,
      arrival_time: document.getElementById('predict-arrival').value,
      acuity_level: Number(document.getElementById('predict-acuity').value),
      department: document.getElementById('predict-department').value,
    };
    const result = await fetchJson('/predictive/er-wait', { method: 'POST', body: JSON.stringify(payload) });
    document.getElementById('predictive-result').innerHTML = `Predicted wait: ${result.predicted_wait_time.toFixed(1)} min (min ${result.min_wait_time.toFixed(1)}, max ${result.max_wait_time.toFixed(1)})`;
  } catch (error) {
    statusMessage('predictive-result', `Error predicting wait: ${error.message}`, true);
  }
}

async function predictBedOccupancy() {
  try {
    const hoursAhead = Number(document.getElementById('forecast-hours').value) || 24;
    const result = await fetchJson(`/predictive/bed-occupancy?hours_ahead=${hoursAhead}`);
    document.getElementById('bed-forecast').innerHTML = `<p>Next ${hoursAhead} hours occupancy forecast:</p><pre>${JSON.stringify(result.predicted_occupancy, null, 2)}</pre>`;
  } catch (error) {
    document.getElementById('bed-forecast').textContent = `Error forecasting occupancy: ${error.message}`;
  }
}

async function predictStaffingDemand() {
  const container = document.getElementById('staffing-forecast');
  try {
    const params = new URLSearchParams({
      hours_ahead: document.getElementById('staffing-hours').value,
      patients_per_staff: document.getElementById('patients-per-staff').value,
    });
    const department = document.getElementById('staffing-department').value;
    if (department) params.set('department', department);
    const forecast = await fetchJson(`/predictive/staffing-demand?${params}`);
    const table = document.createElement('table');
    table.innerHTML = '<thead><tr><th>Hour</th><th>Expected arrivals</th><th>Estimated staff</th></tr></thead>';
    const body = table.createTBody();
    forecast.timestamps.forEach((timestamp, index) => {
      const row = body.insertRow();
      [new Date(timestamp).toLocaleString(), forecast.predicted_patient_arrivals[index],
        forecast.recommended_staff[index]].forEach(value => {
        row.insertCell().textContent = value;
      });
    });
    container.replaceChildren(table);
  } catch (error) {
    container.textContent = `Unable to forecast staffing: ${error.message}`;
  }
}

async function createPatient() {
  try {
    const payload = {
      patient_id: Number(document.getElementById('patient-id').value),
      acuity_level: Number(document.getElementById('patient-acuity').value),
      department: document.getElementById('patient-department').value,
      arrival_time: document.getElementById('patient-arrival').value || null,
    };
    await fetchJson('/patients', { method: 'POST', body: JSON.stringify(payload) });
    statusMessage('patient-create-status', 'Patient created successfully');
    loadPatients();
  } catch (error) {
    statusMessage('patient-create-status', `Create failed: ${error.message}`, true);
  }
}

async function createDoctor() {
  try {
    const payload = {
      doctor_id: document.getElementById('doctor-id').value,
      name: document.getElementById('doctor-name').value,
      specialty: document.getElementById('doctor-specialty').value,
      department: document.getElementById('doctor-department').value,
      is_available: document.getElementById('doctor-available').value === 'true',
    };
    await fetchJson('/doctors', { method: 'POST', body: JSON.stringify(payload) });
    statusMessage('doctor-create-status', 'Doctor created successfully');
    loadDoctors();
  } catch (error) {
    statusMessage('doctor-create-status', `Create failed: ${error.message}`, true);
  }
}

async function createBed() {
  try {
    const payload = {
      bed_number: document.getElementById('bed-number').value,
      department: document.getElementById('bed-department').value,
      room_type: document.getElementById('bed-room-type').value,
    };
    await fetchJson('/beds', { method: 'POST', body: JSON.stringify(payload) });
    statusMessage('bed-create-status', 'Bed created successfully');
    loadBeds();
  } catch (error) {
    statusMessage('bed-create-status', `Create failed: ${error.message}`, true);
  }
}

async function createAppointment() {
  try {
    const payload = {
      appointment_id: document.getElementById('appointment-id').value,
      patient_id: Number(document.getElementById('appointment-patient-id').value),
      doctor_id: Number(document.getElementById('appointment-doctor-id').value),
      scheduled_time: document.getElementById('appointment-time').value,
      duration_minutes: Number(document.getElementById('appointment-duration').value),
      appointment_type: document.getElementById('appointment-type').value,
    };
    await fetchJson('/appointments', { method: 'POST', body: JSON.stringify(payload) });
    statusMessage('appointment-create-status', 'Appointment created successfully');
    loadAppointments();
  } catch (error) {
    statusMessage('appointment-create-status', `Create failed: ${error.message}`, true);
  }
}

async function initializeApp() {
  loadOverview();
  loadPatients();
  loadDoctors();
  loadBeds();
  loadAppointments();
  reloadPredictiveStatus();
  loadAdminSummary();
}

window.addEventListener('load', initializeApp);
