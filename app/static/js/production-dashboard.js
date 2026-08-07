(function () {
    function timers() {
        document.querySelectorAll('[data-start]').forEach(function (node) {
            var seconds = Math.max(0, Math.floor((Date.now() - new Date(node.dataset.start).getTime()) / 1000));
            var h = String(Math.floor(seconds / 3600)).padStart(2, '0');
            var m = String(Math.floor((seconds % 3600) / 60)).padStart(2, '0');
            var s = String(seconds % 60).padStart(2, '0');
            node.querySelector('.elapsed-time').textContent = h + ':' + m + ':' + s;
        });
    }
    timers();
    setInterval(timers, 1000);

    var body = document.getElementById('canli-uretim-body');
    if (!body) return;
    function safe(value) {
        var node = document.createElement('span');
        node.textContent = value == null ? '' : String(value);
        return node.innerHTML;
    }
    function duration(minutes) {
        return Math.floor(minutes / 60) + ' sa ' + (minutes % 60) + ' dk';
    }
    var loading = false;
    function panelVisible() {
        var panel = document.getElementById('uretim-paneli');
        return panel && !panel.hidden && document.visibilityState === 'visible';
    }
    async function refresh() {
        if (!panelVisible() || loading) return;
        loading = true;
        try {
            var response = await fetch('/api/dashboard/uretim-durum', {headers: {'Accept': 'application/json'}});
            if (!response.ok) return;
            var rows = await response.json();
            var stationBoard = document.getElementById('canli-istasyonlar');
            if (stationBoard) {
                var activeRows = rows.filter(function (row) { return row.durum === 'Devam Ediyor'; });
                var groups = {};
                activeRows.forEach(function (row) { (groups[row.istasyon] = groups[row.istasyon] || []).push(row); });
                stationBoard.innerHTML = Object.keys(groups).length ? Object.keys(groups).sort().map(function (station) {
                    return '<article class="live-station-card"><div class="live-station-head"><strong><i class="bi bi-geo-alt me-1"></i>' + safe(station) + '</strong><span>' + groups[station].length + ' çalışan</span></div>' +
                        groups[station].map(function (row) { return '<div class="live-worker"><i class="bi bi-person-gear"></i><div><strong>' + safe(row.operator) + '</strong><small>' + safe(row.operasyon || row.urun) + ' · ' + safe(row.emir_no) + '</small></div><span class="live-worker-time">' + duration(row.sure_dakika) + '</span></div>'; }).join('') + '</article>';
                }).join('') : '<div class="text-muted text-center py-3">Şu anda istasyonda devam eden iş yok.</div>';
            }
            body.innerHTML = rows.length ? rows.map(function (row) {
                var active = row.durum === 'Devam Ediyor';
                return '<tr class="' + (active ? 'table-success' : '') + '">' +
                    '<td><span class="badge ' + (active ? 'bg-success' : 'bg-secondary') + '">' + safe(row.durum) + '</span></td>' +
                    '<td><strong>' + safe(row.operator) + '</strong></td><td>' + safe(row.istasyon) + '</td>' +
                    '<td><strong>' + safe(row.emir_no) + '</strong><div class="small text-muted">' + safe(row.urun) + '</div></td>' +
                    '<td>' + safe(row.baslangic) + '</td><td>' + duration(row.sure_dakika) + '</td>' +
                    '<td>' + safe(row.uretilen_miktar) + ' / <span class="text-danger">' + safe(row.fire_miktari) + '</span></td></tr>';
            }).join('') : '<tr><td colspan="7" class="text-center text-muted py-4">Henüz üretim hareketi yok.</td></tr>';
            document.getElementById('uretim-son-guncelleme').textContent = 'Son güncelleme: ' + new Date().toLocaleTimeString('tr-TR');
        } catch (_) { /* Son başarılı veri ekranda kalır. */ }
        finally { loading = false; }
    }
    refresh();
    setInterval(refresh, 10000);
    document.addEventListener('dashboard:panel-change', function (event) {
        if (event.detail && event.detail.target === 'uretim') refresh();
    });
    document.addEventListener('visibilitychange', function () {
        if (document.visibilityState === 'visible') refresh();
    });
}());
