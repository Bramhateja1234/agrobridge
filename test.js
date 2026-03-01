
    const token = localStorage.getItem('accessToken');
    const userStr = localStorage.getItem('user');

    if (!token || !userStr) window.location.href = '/auth/login/';
    const user = JSON.parse(userStr);

    if (user.role !== 'delivery' && user.role !== 'admin') {
        window.location.href = '/auth/login/';
    }

    document.getElementById('agentName').textContent = user.name || 'Agent';

    let currentOrders = [];

    async function loadOrders() {
        const container = document.getElementById('ordersContainer');
        try {
            const res = await fetch('/api/orders/delivery/orders/', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.status === 401) {
                logout();
                return;
            }
            const data = await res.json();
            currentOrders = data.results || data || [];
            renderOrders();
        } catch {
            container.innerHTML = '<div class="alert alert-danger shadow-sm rounded-4 border-0">Failed to load delivery orders. Please try again.</div>';
        }
    }

    async function loadStats() {
        try {
            const res = await fetch('/api/orders/delivery/stats/', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                document.getElementById('statDelivered').textContent = data.delivered || 0;
                document.getElementById('statCancelled').textContent = data.cancelled || 0;
                document.getElementById('statTotal').textContent = data.total_assigned || 0;
                document.getElementById('statsContainer').style.display = 'flex';

                // Render History
                const tbody = document.getElementById('historyTableBody');
                if (data.history && data.history.length > 0) {
                    tbody.innerHTML = data.history.map(h => `
                        <tr>
                            <td class="ps-4"><span class="fw-bold text-primary">#${h.id}</span></td>
                            <td>${h.consumer_name}</td>
                            <td><span class="badge bg-light text-dark border border-secondary font-monospace small">${h.payment_method.toUpperCase()}</span></td>
                            <td>
                                <span class="badge ${h.order_status === 'delivered' ? 'bg-success' : 'bg-danger'} text-white rounded-pill text-uppercase" style="font-size: 0.70rem">
                                    ${h.order_status.replace('_', ' ')}
                                </span>
                            </td>
                            <td class="pe-4 text-muted small"><i class="bi bi-clock me-1"></i>${new Date(h.updated_at).toLocaleString()}</td>
                        </tr>
                    `).join('');
                } else {
                    tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-muted">No recent trips found.</td></tr>';
                }
            }
        } catch (err) {
            console.error("Failed to load delivery stats", err);
        }
    }

    function renderOrders() {
        const container = document.getElementById('ordersContainer');

        // Filter rules
        // Only show active deliveries (not delivered/cancelled)
        let filtered = currentOrders.filter(o => !['delivered', 'cancelled'].includes(o.order_status));

        if (filtered.length === 0) {
            container.innerHTML = `
                <div class="text-center py-5 bg-white rounded-4 shadow-sm">
                    <i class="bi bi-box-seam fs-1 text-muted"></i>
                    <h5 class="fw-bold mt-3 text-secondary">No active deliveries.</h5>
                    <p class="text-muted small">You currently have no orders assigned to you. Check back later.</p>
                </div>`;
            return;
        }

        container.innerHTML = `<div class="row g-4">${filtered.map(o => `
            <div class="col-md-6 col-lg-4">
                <div class="card h-100 border-0 shadow-sm rounded-4 position-relative hover-lift">
                    <div class="card-body p-4">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <span class="badge ${o.payment_method === 'cod' ? 'bg-warning text-dark' : 'bg-success'} rounded-pill">
                                <i class="bi bi-currency-rupee me-1"></i>${o.payment_method.toUpperCase()}
                            </span>
                            <span class="fw-bold text-muted small">#${o.id}</span>
                        </div>
                        
                        <h5 class="fw-bold text-dark mb-1">${o.crop_name} <span class="text-success">(${o.quantity}kg)</span></h5>
                        <p class="text-muted small mb-4"><i class="bi bi-person me-1"></i>By ${o.farmer_name}</p>

                        <div class="bg-light p-3 rounded-3 mb-4">
                            <div class="d-flex mb-2">
                                <i class="bi bi-geo-alt-fill text-danger mt-1 me-2"></i>
                                <div>
                                    <small class="text-muted d-block fw-bold">Deliver To:</small>
                                    <span class="small">${o.delivery_address || 'Address not provided'}</span>
                                </div>
                            </div>
                            <div class="d-flex">
                                <i class="bi bi-person-fill text-primary mt-1 me-2"></i>
                                <div>
                                    <small class="text-muted d-block fw-bold">Customer:</small>
                                    <span class="small">${o.consumer_name}</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="d-grid gap-2">
                            ${o.order_status === 'picked_up' ? `
                                <button class="btn btn-primary rounded-3 py-2 fw-bold shadow-sm" onclick="updateOrderStatus(${o.id}, 'out_for_delivery')">
                                    <i class="bi bi-truck me-1"></i> Mark Out for Delivery
                                </button>
                            ` : ''}
                            ${o.order_status === 'out_for_delivery' ? `
                                <button class="btn btn-info text-white rounded-3 py-2 fw-bold shadow-sm mb-2" onclick="updateLocation(${o.id})">
                                    <i class="bi bi-geo-alt-fill me-1"></i> Move Towards Customer
                                </button>
                                <button class="btn btn-success rounded-3 py-2 fw-bold shadow-sm" onclick="startScanner(${o.id}, 'delivered', 'DELIVERY-${o.id}')">
                                    <i class="bi bi-qr-code-scan me-1"></i> Scan to Mark Delivered
                                </button>
                                <button class="btn btn-outline-success rounded-3 py-1 btn-sm shadow-sm" onclick="promptDeliveryPayment(${o.id})">
                                    Manual Override
                                </button>
                            ` : ''}
                            ${o.order_status === 'confirmed' ? `
                                <button class="btn btn-warning text-dark rounded-3 py-2 fw-bold shadow-sm" onclick="startScanner(${o.id}, 'picked_up', 'PICKUP-${o.id}')">
                                    <i class="bi bi-qr-code-scan me-1"></i> Scan to Mark Picked Up
                                </button>
                                <button class="btn btn-outline-warning text-dark rounded-3 py-1 btn-sm shadow-sm" onclick="updateOrderStatus(${o.id}, 'picked_up')">
                                    Manual Override
                                </button>
                            `: ''}
                        </div>
                    </div>
                </div>
            </div>
        `).join('')}</div>`;
    }

    // Payment Modal Logic
    let currentPaymentOrderId = null;
    function promptDeliveryPayment(orderId) {
        const order = currentOrders.find(o => o.id === orderId);
        if (!order) return;

        // If it's already paid online or not COD, just strictly mark delivered
        if (order.payment_method !== 'cod' || order.payment_status === 'paid') {
            updateOrderStatus(orderId, 'delivered');
            return;
        }

        // Otherwise, it's COD and unpaid: show payment modal
        currentPaymentOrderId = orderId;
        document.getElementById('paymentModalAmount').textContent = '₹' + parseFloat(order.total_price).toFixed(2);
        const modal = new bootstrap.Modal(document.getElementById('paymentModal'));
        modal.show();
    }

    async function processCashPayment() {
        if (!currentPaymentOrderId) return;
        // Cash means we just mark it delivered (backend auto-sets to paid)
        await updateOrderStatus(currentPaymentOrderId, 'delivered', true, 'cash');
        const modalEl = document.getElementById('paymentModal');
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();
    }

    async function generateStripeLink() {
        if (!currentPaymentOrderId) return;
        const btn = document.getElementById('btnStripeLink');
        const origText = btn.innerHTML;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Generating...';
        btn.disabled = true;

        try {
            const res = await fetch('/api/payments/checkout/', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ order_id: currentPaymentOrderId })
            });
            const data = await res.json();
            if (res.ok && data.checkout_url) {
                // Open Stripe Checkout in a new tab for the customer to pay
                window.open(data.checkout_url, '_blank');
                // Could ideally poll for status, but for MVP we instruct agent to wait

                // Show the Verify button instead of regenerating
                btn.classList.add('d-none');
                btn.innerHTML = '<i class="bi bi-link-45deg me-1"></i> Generate Payment Link'; // reset
                btn.disabled = false;

                const verifyBtn = document.getElementById('btnVerifyLink');
                verifyBtn.classList.remove('d-none');
                verifyBtn.dataset.sessionId = data.session_id;

                alert("Payment link generated! Have the customer complete payment, then click 'Verify Online Payment'.");
            } else {
                alert(data.error || 'Failed to generate link.');
            }
        } catch (e) {
            alert('Network error.');
        } finally {
            btn.innerHTML = origText;
            btn.disabled = false;
        }
    }

    async function verifyOnlinePayment() {
        const verifyBtn = document.getElementById('btnVerifyLink');
        const sessionId = verifyBtn.dataset.sessionId;
        if (!sessionId) return;

        const origText = verifyBtn.innerHTML;
        verifyBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Verifying...';
        verifyBtn.disabled = true;

        try {
            const res = await fetch('/api/payments/verify/', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ session_id: sessionId })
            });
            const data = await res.json();
            if (res.ok && data.status === 'paid') {
                alert("Payment Confirmed! Order is now marked as Delivered.");
                const modalEl = document.getElementById('paymentModal');
                const modal = bootstrap.Modal.getInstance(modalEl);
                if (modal) modal.hide();
                await loadOrders();
                await loadStats();
            } else {
                alert(data.message || "Payment is still pending. Customer has not completed it yet.");
                verifyBtn.innerHTML = origText;
                verifyBtn.disabled = false;
            }
        } catch {
            alert("Error verifying payment connect to server.");
            verifyBtn.innerHTML = origText;
            verifyBtn.disabled = false;
        }
    }

    document.getElementById('paymentModal').addEventListener('hidden.bs.modal', function () {
        const btnStripe = document.getElementById('btnStripeLink');
        const btnVerify = document.getElementById('btnVerifyLink');
        if (btnStripe) {
            btnStripe.classList.remove('d-none');
            btnStripe.innerHTML = '<i class="bi bi-link-45deg fs-5 me-2 align-middle"></i> Pay with Link / Card';
            btnStripe.disabled = false;
        }
        if (btnVerify) btnVerify.classList.add('d-none');
    });

    let html5QrcodeScanner = null;

    function startScanner(orderId, nextStatus, expectedCode) {
        const order = currentOrders.find(o => o.id === orderId);
        if (!order) return;

        const container = document.getElementById('ordersContainer');
        const originalContent = container.innerHTML;

        container.innerHTML = `
            <div class="card border-0 shadow-sm rounded-4 mt-3">
                <div class="card-body p-4 text-center">
                    <h5 class="fw-bold mb-3">Scan QR Code for Order #${orderId}</h5>
                    <p class="text-muted small">Proceeding to status: <strong>${nextStatus.toUpperCase()}</strong></p>
                    <div id="qr-reader" class="mx-auto" style="max-width: 400px;"></div>
                    <button class="btn btn-secondary mt-4 w-100" onclick="cancelScanner()">Cancel Scan</button>
                </div>
            </div>
        `;

        if (typeof Html5QrcodeScanner !== 'undefined') {
            html5QrcodeScanner = new Html5QrcodeScanner("qr-reader", { fps: 10, qrbox: { width: 250, height: 250 } });
            html5QrcodeScanner.render((decodedText) => {
                if (decodedText === expectedCode) {
                    html5QrcodeScanner.clear();
                    html5QrcodeScanner = null;
                    if (nextStatus === 'delivered') {
                        promptDeliveryPayment(orderId);
                    } else {
                        updateOrderStatus(orderId, nextStatus);
                    }
                } else {
                    alert('Invalid QR Code. This does not match the expected ' + expectedCode);
                }
            }, (err) => {
                // Ignore errors
            });
        } else {
            container.innerHTML = `<div class="alert alert-warning">Scanner library not loaded. Please use Manual Override. <br><button class="btn btn-secondary mt-2" onclick="cancelScanner()">Go Back</button></div>`;
        }
    }

    function cancelScanner() {
        if (html5QrcodeScanner) {
            html5QrcodeScanner.clear();
            html5QrcodeScanner = null;
        }
        renderOrders();
    }

    async function updateOrderStatus(orderId, newStatus, skipConfirm = false, codPaymentType = null) {
        if (!skipConfirm && !confirm(`Are you sure you want to change this order status to ${newStatus.replace('_', ' ').toUpperCase()}?`)) return;

        const body = { order_status: newStatus };
        if (codPaymentType) body.cod_payment_type = codPaymentType;

        try {
            const res = await fetch(`/api/orders/${orderId}/status/`, {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(body)
            });

            if (res.ok) {
                // Refresh data
                await loadOrders();
                await loadStats();
            } else {
                const data = await res.json();
                alert('Error updating status: ' + (data.error || JSON.stringify(data)));
            }
        } catch (err) {
            alert('Network error while updating status.');
        }
    }

    async function updateLocation(orderId) {
        try {
            const res = await fetch(`/api/orders/${orderId}/location/`, {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (res.ok) {
                alert('GPS Location incremented by 0.0005! Check consumer map view.');
            } else {
                alert('Error updating location.');
            }
        } catch (err) {
            alert('Network error.');
        }
    }

    function logout() {
        localStorage.clear();
        window.location.href = '/auth/login/';
    }

    // Initialize
    loadOrders();
    loadStats();
