document.addEventListener('DOMContentLoaded', function() {
    const ticketId = document.getElementById('ticket-detail')?.dataset.ticketId;
    
    if (ticketId) {
        const ws = new WebSocket(
            `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/tickets/${ticketId}/`
        );

        ws.onmessage = function(e) {
            const data = JSON.parse(e.data);
            if (data.type === 'ticket_update') {
                updateTicketStatus(data);
            } else if (data.type === 'new_message') {
                addNewMessage(data.message);
            }
        };
    }
});

function updateTicketStatus(data) {
    const statusElement = document.querySelector('.ticket-status');
    if (statusElement) {
        statusElement.textContent = data.status;
        statusElement.className = `ticket-status ${data.status.toLowerCase()}`;
    }
}

function addNewMessage(message) {
    const messagesSection = document.querySelector('.messages-section');
    if (messagesSection) {
        const messageHtml = `
            <div class="message-box ${message.is_staff_reply ? 'staff-message' : 'user-message'}">
                <div class="message-meta">
                    <strong>${message.user_name}</strong>
                    <small class="text-muted ml-2">${message.created}</small>
                </div>
                <div class="message-content mt-2">
                    ${message.message}
                </div>
            </div>
        `;
        messagesSection.insertAdjacentHTML('beforeend', messageHtml);
    }
} 