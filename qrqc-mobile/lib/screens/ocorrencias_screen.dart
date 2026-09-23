import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../services/api_service.dart';
import '../models/models.dart';
import '../widgets/severity_chip.dart';

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
        onPressed: () async {
          final criou = await Navigator.push<bool>(
            context,
            MaterialPageRoute(
                builder: (_) => const _NovaOcorrenciaScreen()),
          );
          if (criou == true) _load();
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

class _NovaOcorrenciaScreen extends StatefulWidget {
  const _NovaOcorrenciaScreen();
  @override
  State<_NovaOcorrenciaScreen> createState() => _NovaOcorrenciaScreenState();
}

class _NovaOcorrenciaScreenState extends State<_NovaOcorrenciaScreen> {
  final _formKey = GlobalKey<FormState>();
  final _descCtrl = TextEditingController();
  List<Maquina> _maquinas = [];
  Maquina? _maquina;
  String _tipo = 'Falha mecânica';
  String _impacto = 'Médio';
  bool _saving = false;

  static const _tipos = [
    'Falha mecânica', 'Falha elétrica', 'Falha hidráulica',
    'Falha pneumática', 'Desgaste', 'Outro',
  ];
  static const _impactos = ['Crítico', 'Alto', 'Médio', 'Baixo'];

  @override
  void initState() {
    super.initState();
    ApiService().getMaquinas().then((list) {
      if (mounted) setState(() => _maquinas = list);
    });
  }

  @override
  void dispose() {
    _descCtrl.dispose();
    super.dispose();
  }

  Future<void> _salvar() async {
    if (!_formKey.currentState!.validate()) return;
    if (_maquina == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text('Selecione a máquina'),
            backgroundColor: Color(0xFFEF4444)),
      );
      return;
    }
    setState(() => _saving = true);
    try {
      await ApiService().criarOcorrencia({
        'maquina_id': _maquina!.id,
        'descricao': _descCtrl.text.trim(),
        'tipo_ocorrencia': _tipo,
        'nivel_impacto': _impacto,
      });
      if (!mounted) return;
      Navigator.pop(context, true);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
            content: Text(e.toString()),
            backgroundColor: const Color(0xFFEF4444)),
      );
    } finally {
      if (mounted) setState(() => _saving = false);
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
          icon: const Icon(Icons.close, color: Colors.white, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text('Nova Ocorrência',
            style: TextStyle(color: Colors.white, fontSize: 16)),
      ),
      body: SafeArea(
        child: Form(
          key: _formKey,
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _label('Máquina'),
                DropdownButtonFormField<Maquina>(
                  value: _maquina,
                  dropdownColor: const Color(0xFF0F1F35),
                  style:
                      const TextStyle(color: Colors.white, fontSize: 14),
                  decoration: _deco('Selecionar máquina'),
                  items: _maquinas
                      .map((m) => DropdownMenuItem(
                            value: m,
                            child: Text(m.nome),
                          ))
                      .toList(),
                  onChanged: (v) => setState(() => _maquina = v),
                ),
                const SizedBox(height: 16),
                _label('Tipo'),
                DropdownButtonFormField<String>(
                  value: _tipo,
                  dropdownColor: const Color(0xFF0F1F35),
                  style:
                      const TextStyle(color: Colors.white, fontSize: 14),
                  decoration: _deco('Selecionar tipo'),
                  items: _tipos
                      .map((t) => DropdownMenuItem(value: t, child: Text(t)))
                      .toList(),
                  onChanged: (v) => setState(() => _tipo = v ?? _tipo),
                ),
                const SizedBox(height: 16),
                _label('Nível de impacto'),
                DropdownButtonFormField<String>(
                  value: _impacto,
                  dropdownColor: const Color(0xFF0F1F35),
                  style:
                      const TextStyle(color: Colors.white, fontSize: 14),
                  decoration: _deco('Selecionar impacto'),
                  items: _impactos
                      .map((i) => DropdownMenuItem(value: i, child: Text(i)))
                      .toList(),
                  onChanged: (v) => setState(() => _impacto = v ?? _impacto),
                ),
                const SizedBox(height: 16),
                _label('Descrição'),
                TextFormField(
                  controller: _descCtrl,
                  style:
                      const TextStyle(color: Colors.white, fontSize: 14),
                  decoration: _deco('Descreva o problema observado…'),
                  maxLines: 4,
                  validator: (v) => v == null || v.trim().isEmpty
                      ? 'Descreva o problema'
                      : null,
                ),
                const SizedBox(height: 28),
                SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: ElevatedButton(
                    onPressed: _saving ? null : _salvar,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFFF59E0B),
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10)),
                    ),
                    child: _saving
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                                color: Colors.white, strokeWidth: 2))
                        : const Text('Registrar Ocorrência',
                            style: TextStyle(
                                color: Colors.white,
                                fontSize: 15,
                                fontWeight: FontWeight.w600)),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _label(String text) => Padding(
        padding: const EdgeInsets.only(bottom: 6),
        child: Text(text,
            style: const TextStyle(
                color: Colors.white54,
                fontSize: 12,
                fontWeight: FontWeight.w500)),
      );

  InputDecoration _deco(String hint) => InputDecoration(
        hintText: hint,
        hintStyle: const TextStyle(color: Colors.white24, fontSize: 13),
        filled: true,
        fillColor: const Color(0xFF0F1F35),
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: Colors.white12),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: Colors.white12),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide:
              const BorderSide(color: Color(0xFFF59E0B), width: 1.5),
        ),
        errorStyle: const TextStyle(color: Color(0xFFEF4444)),
      );
}
