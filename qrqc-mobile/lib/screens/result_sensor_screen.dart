import 'package:flutter/material.dart';
import '../models/models.dart';
import '../widgets/severity_chip.dart';

class ResultSensorScreen extends StatelessWidget {
  final ResultadoSensor resultado;

  const ResultSensorScreen({super.key, required this.resultado});

  @override
  Widget build(BuildContext context) {
    final anomalias = resultado.anomalias;
    final semAnomalia = anomalias.isEmpty;

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
        title: const Text(
          'Resultado da Inspeção',
          style: TextStyle(color: Colors.white, fontSize: 16),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Score + resumo
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: const Color(0xFF0F1F35),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: Colors.white12),
                ),
                child: Column(
                  children: [
                    HealthGauge(resultado.score),
                    const SizedBox(height: 16),
                    Text(
                      resultado.resumo,
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                          color: Colors.white70, fontSize: 13),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Modelo: ${resultado.modelo}',
                      style: const TextStyle(
                          color: Colors.white24, fontSize: 11),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              if (semAnomalia)
                _emptyState()
              else ...[
                Text(
                  '${anomalias.length} anomalia(s) detectada(s)',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 12),
                ...anomalias.asMap().entries.map((e) =>
                    _AnomaliaCard(numero: e.key + 1, anomalia: e.value)),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _emptyState() => Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: const Color(0xFF22C55E).withOpacity(0.08),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
              color: const Color(0xFF22C55E).withOpacity(0.25)),
        ),
        child: const Column(
          children: [
            Icon(Icons.check_circle_outline,
                color: Color(0xFF22C55E), size: 40),
            SizedBox(height: 12),
            Text(
              'Nenhuma anomalia detectada',
              style: TextStyle(
                  color: Color(0xFF22C55E),
                  fontSize: 15,
                  fontWeight: FontWeight.w600),
            ),
            SizedBox(height: 4),
            Text(
              'O equipamento parece em condição normal.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.white54, fontSize: 13),
            ),
          ],
        ),
      );
}

class _AnomaliaCard extends StatefulWidget {
  final int numero;
  final Anomalia anomalia;

  const _AnomaliaCard({required this.numero, required this.anomalia});

  @override
  State<_AnomaliaCard> createState() => _AnomaliaCardState();
}

class _AnomaliaCardState extends State<_AnomaliaCard> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final a = widget.anomalia;
    final borderColor = switch (a.severidade) {
      'critico' => const Color(0xFFEF4444),
      'atencao' => const Color(0xFFF59E0B),
      _ => const Color(0xFF3B82F6),
    };

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: const Color(0xFF0F1F35),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: borderColor.withOpacity(0.3)),
      ),
      child: Column(
        children: [
          InkWell(
            borderRadius: const BorderRadius.vertical(
                top: Radius.circular(12),
                bottom: Radius.circular(12)),
            onTap: () => setState(() => _expanded = !_expanded),
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Row(
                children: [
                  Container(
                    width: 28,
                    height: 28,
                    decoration: BoxDecoration(
                      color: borderColor.withOpacity(0.15),
                      shape: BoxShape.circle,
                    ),
                    child: Center(
                      child: Text(
                        '${widget.numero}',
                        style: TextStyle(
                          color: borderColor,
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          a.rotulo,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          a.componente,
                          style: const TextStyle(
                              color: Colors.white38, fontSize: 12),
                        ),
                      ],
                    ),
                  ),
                  SeverityChip(a.severidade, small: true),
                  const SizedBox(width: 6),
                  Icon(
                    _expanded
                        ? Icons.keyboard_arrow_up
                        : Icons.keyboard_arrow_down,
                    color: Colors.white38,
                    size: 18,
                  ),
                ],
              ),
            ),
          ),
          if (_expanded)
            Padding(
              padding: const EdgeInsets.fromLTRB(14, 0, 14, 14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Divider(color: Colors.white12),
                  _info('Descrição', a.descricao),
                  if (a.causaProvavel.isNotEmpty)
                    _info('Causa provável', a.causaProvavel),
                  _info('Recomendação', a.recomendacao),
                  const SizedBox(height: 4),
                  Text(
                    'Confiança: ${(a.confianca * 100).round()}%',
                    style: const TextStyle(
                        color: Colors.white24, fontSize: 11),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Widget _info(String label, String text) => Padding(
        padding: const EdgeInsets.only(bottom: 8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label,
                style: const TextStyle(
                    color: Colors.white38,
                    fontSize: 11,
                    fontWeight: FontWeight.w600)),
            const SizedBox(height: 2),
            Text(text,
                style:
                    const TextStyle(color: Colors.white70, fontSize: 13)),
          ],
        ),
      );
}
