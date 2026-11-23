import 'package:flutter/material.dart';
import '../models/models.dart';
import '../widgets/severity_chip.dart';

class ResultDocScreen extends StatelessWidget {
  final ResultadoDocumento resultado;

  const ResultDocScreen({super.key, required this.resultado});

  @override
  Widget build(BuildContext context) {
    final problemas = resultado.problemas;
    final conferencias = resultado.conferencias
        .where((c) => c.severidade != 'info' || resultado.aprovado)
        .toList();
    // "Sem problemas" só quando o documento foi aprovado na conferência com o cadastro:
    // uma PT bem preenchida com executante sem NR-10 válida continua BLOQUEADA
    final semProblema =
        problemas.isEmpty && conferencias.isEmpty && resultado.aprovado;
    final score = resultado.score;

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
              _StatusDoc(resultado.status),
              const SizedBox(height: 14),
              // Placar + resumo
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: const Color(0xFF0F1F35),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: Colors.white12),
                ),
                child: Column(
                  children: [
                    _ScoreDoc(score),
                    const SizedBox(height: 14),
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

              if (conferencias.isNotEmpty) ...[
                const Text(
                  'Conferência com o cadastro da empresa',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 12),
                ...conferencias.map((c) => _ConferenciaCard(c)),
                const SizedBox(height: 10),
              ],
              if (semProblema)
                _emptyState()
              else if (problemas.isNotEmpty) ...[
                Text(
                  '${problemas.length} problema(s) encontrado(s)',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 12),
                ...problemas.asMap().entries.map((e) =>
                    _ProblemaCard(numero: e.key + 1, problema: e.value)),
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
          color: const Color(0xFF22C55E).withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
              color: const Color(0xFF22C55E).withValues(alpha: 0.25)),
        ),
        child: const Column(
          children: [
            Icon(Icons.check_circle_outline,
                color: Color(0xFF22C55E), size: 40),
            SizedBox(height: 12),
            Text(
              'Documento sem problemas detectados',
              style: TextStyle(
                  color: Color(0xFF22C55E),
                  fontSize: 15,
                  fontWeight: FontWeight.w600),
            ),
            SizedBox(height: 4),
            Text(
              'A Nexa IA não identificou erros visíveis neste documento.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.white54, fontSize: 13),
            ),
          ],
        ),
      );
}

class _StatusDoc extends StatelessWidget {
  final String status;
  const _StatusDoc(this.status);

  @override
  Widget build(BuildContext context) {
    final (icone, cor, titulo, texto) = switch (status) {
      'bloqueado' => (
          Icons.block,
          const Color(0xFFEF4444),
          'BLOQUEADO',
          'Não libere o serviço: há pendência de habilitação ou de cadastro.',
        ),
      'aprovado' => (
          Icons.verified_outlined,
          const Color(0xFF22C55E),
          'APROVADO',
          'Documento conferido com o cadastro da empresa.',
        ),
      _ => (
          Icons.warning_amber_rounded,
          const Color(0xFFF59E0B),
          'COM PENDÊNCIAS',
          'Corrija os itens abaixo antes de liberar.',
        ),
    };
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: cor.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: cor.withValues(alpha: 0.5), width: 1.5),
      ),
      child: Row(
        children: [
          Icon(icone, color: cor, size: 34),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  titulo,
                  style: TextStyle(
                      color: cor,
                      fontSize: 18,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 0.5),
                ),
                const SizedBox(height: 2),
                Text(texto,
                    style:
                        const TextStyle(color: Colors.white70, fontSize: 12.5)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ConferenciaCard extends StatelessWidget {
  final ConferenciaDocumento c;
  const _ConferenciaCard(this.c);

  @override
  Widget build(BuildContext context) {
    final cor = switch (c.severidade) {
      'alto' => const Color(0xFFEF4444),
      'medio' => const Color(0xFFF59E0B),
      'baixo' => const Color(0xFF3B82F6),
      _ => Colors.white38,
    };
    final icone = switch (c.categoria) {
      'habilitacao' => Icons.badge_outlined,
      'validade' => Icons.event_outlined,
      'equipamento' => Icons.precision_manufacturing_outlined,
      _ => Icons.person_search_outlined,
    };
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF0F1F35),
        borderRadius: BorderRadius.circular(12),
        border: Border(left: BorderSide(color: cor, width: 3)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icone, color: cor, size: 18),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  c.titulo,
                  style: const TextStyle(
                      color: Colors.white,
                      fontSize: 13,
                      fontWeight: FontWeight.w600),
                ),
                if (c.descricao.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(c.descricao,
                      style:
                          const TextStyle(color: Colors.white60, fontSize: 12)),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ScoreDoc extends StatelessWidget {
  final int score;
  const _ScoreDoc(this.score);

  @override
  Widget build(BuildContext context) {
    final color = score >= 90
        ? const Color(0xFF22C55E)
        : score >= 70
            ? const Color(0xFFF59E0B)
            : const Color(0xFFEF4444);
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(Icons.document_scanner_outlined, color: color, size: 32),
        const SizedBox(width: 12),
        Flexible(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '$score / 100',
                style: TextStyle(
                    color: color,
                    fontSize: 28,
                    fontWeight: FontWeight.w800),
              ),
              Text(
                'Qualidade do documento',
                style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.4), fontSize: 12),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _ProblemaCard extends StatelessWidget {
  final int numero;
  final ProblemaDocumento problema;

  const _ProblemaCard({required this.numero, required this.problema});

  @override
  Widget build(BuildContext context) {
    final p = problema;
    final (icon, color) = switch (p.tipo) {
      'erro_calculo' => (Icons.calculate_outlined, const Color(0xFFEF4444)),
      'campo_incorreto' => (Icons.edit_off_outlined, const Color(0xFFF59E0B)),
      'dado_faltante' => (Icons.remove_circle_outline, const Color(0xFFEF4444)),
      'inconsistencia' => (Icons.compare_arrows_outlined, const Color(0xFFF59E0B)),
      'erro_ortografico' => (Icons.spellcheck, const Color(0xFF3B82F6)),
      _ => (Icons.warning_amber_outlined, const Color(0xFFF59E0B)),
    };

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF0F1F35),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withValues(alpha: 0.25)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 32,
                height: 32,
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(icon, color: color, size: 16),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      p.campo.isNotEmpty ? p.campo : _tipoLabel(p.tipo),
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    Text(
                      _tipoLabel(p.tipo),
                      style: const TextStyle(
                          color: Colors.white38, fontSize: 11),
                    ),
                  ],
                ),
              ),
              SeverityChip(p.severidade, small: true),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            p.descricao,
            style: const TextStyle(color: Colors.white70, fontSize: 13),
          ),
          if (p.sugestao.isNotEmpty) ...[
            const SizedBox(height: 8),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(Icons.lightbulb_outline,
                    color: Color(0xFFF59E0B), size: 14),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    p.sugestao,
                    style: const TextStyle(
                        color: Color(0xFFF59E0B), fontSize: 12),
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  String _tipoLabel(String tipo) => switch (tipo) {
        'erro_calculo' => 'Erro de cálculo',
        'campo_incorreto' => 'Campo incorreto',
        'dado_faltante' => 'Dado faltante',
        'inconsistencia' => 'Inconsistência',
        'erro_ortografico' => 'Erro ortográfico',
        _ => tipo,
      };
}
