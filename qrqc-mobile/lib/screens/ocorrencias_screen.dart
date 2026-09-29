import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../services/api_service.dart';
import '../models/models.dart';
import '../widgets/severity_chip.dart';
import 'nova_ocorrencia_screen.dart';

class OcorrenciasScreen extends StatefulWidget {
  const OcorrenciasScreen({super.key});
  @override
  State<OcorrenciasScreen> createState() => _OcorrenciasScreenState();
}

class _OcorrenciasScreenState extends State<OcorrenciasScreen> {
  List<Ocorrencia> _ocorrencias = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final list = await ApiService().getOcorrencias();
      if (mounted) setState(() => _ocorrencias = list);
    } catch (e) {
      if (mounted) setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A1628),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0A1628),
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new,
              color: Colors.white, size: 18),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text('Ocorrências',
            style: TextStyle(color: Colors.white, fontSize: 16)),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: Colors.white54, size: 20),
            onPressed: _load,
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        backgroundColor: const Color(0xFFF59E0B),
        tooltip: 'Nova ocorrência',
        onPressed: () async {
          final id = await Navigator.push<int>(
            context,
            MaterialPageRoute(builder: (_) => const NovaOcorrenciaScreen()),
          );
          if (id == null || !context.mounted) return;
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text('Ocorrência nº $id registrada. O diagnóstico da IA fica pronto em instantes.'),
            backgroundColor: const Color(0xFF22C55E),
            behavior: SnackBarBehavior.floating,
          ));
          _load();
        },
        child: const Icon(Icons.add, color: Colors.white),
      ),
      body: _loading
          ? const Center(
              child: CircularProgressIndicator(
                  color: Color(0xFF0EA5E9), strokeWidth: 2))
          : _error != null
              ? Center(
                  child: Text(_error!,
                      style:
                          const TextStyle(color: Colors.white54)))
              : _ocorrencias.isEmpty
                  ? const Center(
                      child: Text('Nenhuma ocorrência encontrada',
                          style: TextStyle(color: Colors.white54)))
                  : RefreshIndicator(
                      onRefresh: _load,
                      color: const Color(0xFF0EA5E9),
                      backgroundColor: const Color(0xFF0F1F35),
                      child: ListView.separated(
                        padding: const EdgeInsets.all(16),
                        itemCount: _ocorrencias.length,
                        separatorBuilder: (_, __) =>
                            const SizedBox(height: 8),
                        itemBuilder: (_, i) =>
                            _OcorrenciaCard(_ocorrencias[i]),
                      ),
                    ),
    );
  }
}

class _OcorrenciaCard extends StatelessWidget {
  final Ocorrencia oc;
  const _OcorrenciaCard(this.oc);

  @override
  Widget build(BuildContext context) {
    final statusColor = switch (oc.status) {
      'Resolvida' => const Color(0xFF22C55E),
      'Em andamento' => const Color(0xFFF59E0B),
      _ => const Color(0xFFEF4444),
    };

    String dataFmt = oc.dataOcorrencia;
    try {
      final dt = DateTime.parse(oc.dataOcorrencia);
      dataFmt = DateFormat('dd/MM/yyyy').format(dt);
    } catch (_) {}

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF0F1F35),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  oc.maquinaNome,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: statusColor.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  oc.status,
                  style:
                      TextStyle(color: statusColor, fontSize: 11),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            oc.descricao,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style:
                const TextStyle(color: Colors.white60, fontSize: 13),
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              SeverityChip(
                switch (oc.nivelImpacto) {
                  'Crítico' => 'critico',
                  'Alto' => 'critico',
                  'Médio' => 'atencao',
                  _ => 'info',
                },
                small: true,
              ),
              const SizedBox(width: 8),
              Text(
                oc.tipoOcorrencia,
                style:
                    const TextStyle(color: Colors.white38, fontSize: 11),
              ),
              const Spacer(),
              Text(
                dataFmt,
                style:
                    const TextStyle(color: Colors.white38, fontSize: 11),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
