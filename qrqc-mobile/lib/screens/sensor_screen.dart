import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../services/api_service.dart';
import '../models/models.dart';
import 'result_sensor_screen.dart';

class SensorScreen extends StatefulWidget {
  const SensorScreen({super.key});
  @override
  State<SensorScreen> createState() => _SensorScreenState();
}

class _SensorScreenState extends State<SensorScreen> {
  final _picker = ImagePicker();
  final _ctxCtrl = TextEditingController();
  File? _foto;
  bool _analisando = false;
  List<Maquina> _maquinas = [];
  Maquina? _maquinaSel;

  @override
  void initState() {
    super.initState();
    _loadMaquinas();
  }

  @override
  void dispose() {
    _ctxCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadMaquinas() async {
    try {
      final list = await ApiService().getMaquinas();
      if (mounted) setState(() => _maquinas = list);
    } catch (_) {}
  }

  Future<void> _capturar(ImageSource source) async {
    final xfile = await _picker.pickImage(
      source: source,
      maxWidth: 1920,
      maxHeight: 1920,
      imageQuality: 85,
    );
    if (xfile != null && mounted) {
      setState(() => _foto = File(xfile.path));
    }
  }

  Future<void> _analisar() async {
    if (_foto == null) return;
    setState(() => _analisando = true);
    try {
      final resultado = await ApiService().analisarEquipamento(
        _foto!,
        contexto: _ctxCtrl.text.trim(),
        maquinaId: _maquinaSel?.id,
      );
      if (!mounted) return;
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => ResultSensorScreen(resultado: resultado),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      _showError(e.toString());
    } finally {
      if (mounted) setState(() => _analisando = false);
    }
  }

  void _showError(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(msg),
        backgroundColor: const Color(0xFFEF4444),
        behavior: SnackBarBehavior.floating,
      ),
    );
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
        title: const Text(
          'Sensor Visual',
          style: TextStyle(color: Colors.white, fontSize: 16),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Foto
              GestureDetector(
                onTap: () => _showPickOptions(),
                child: Container(
                  height: 220,
                  width: double.infinity,
                  decoration: BoxDecoration(
                    color: const Color(0xFF0F1F35),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: _foto == null
                          ? Colors.white12
                          : const Color(0xFF0EA5E9).withOpacity(0.4),
                    ),
                  ),
                  child: _foto == null
                      ? const Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.camera_alt_outlined,
                                color: Colors.white24, size: 40),
                            SizedBox(height: 8),
                            Text(
                              'Toque para fotografar\nou escolher da galeria',
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                  color: Colors.white38, fontSize: 13),
                            ),
                          ],
                        )
                      : ClipRRect(
                          borderRadius: BorderRadius.circular(12),
                          child: Image.file(_foto!, fit: BoxFit.cover),
                        ),
                ),
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: _btn(
                      icon: Icons.camera_alt_outlined,
                      label: 'Câmera',
                      onTap: () => _capturar(ImageSource.camera),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: _btn(
                      icon: Icons.photo_library_outlined,
                      label: 'Galeria',
                      onTap: () => _capturar(ImageSource.gallery),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // Máquina
              if (_maquinas.isNotEmpty) ...[
                const Text('Máquina (opcional)',
                    style: TextStyle(
                        color: Colors.white54,
                        fontSize: 12,
                        fontWeight: FontWeight.w500)),
                const SizedBox(height: 6),
                DropdownButtonFormField<Maquina>(
                  value: _maquinaSel,
                  dropdownColor: const Color(0xFF0F1F35),
                  style: const TextStyle(color: Colors.white, fontSize: 14),
                  decoration: _inputDeco('Selecionar máquina'),
                  items: [
                    const DropdownMenuItem(value: null, child: Text('— nenhuma —', style: TextStyle(color: Colors.white38))),
                    ..._maquinas.map((m) => DropdownMenuItem(
                          value: m,
                          child: Text(m.nome),
                        )),
                  ],
                  onChanged: (v) => setState(() => _maquinaSel = v),
                ),
                const SizedBox(height: 16),
              ],

              // Contexto
              const Text('Contexto (opcional)',
                  style: TextStyle(
                      color: Colors.white54,
                      fontSize: 12,
                      fontWeight: FontWeight.w500)),
              const SizedBox(height: 6),
              TextFormField(
                controller: _ctxCtrl,
                style: const TextStyle(color: Colors.white, fontSize: 14),
                decoration: _inputDeco(
                    'Ex: ruído no mancal esquerdo, vibração excessiva…'),
                maxLines: 2,
              ),
              const SizedBox(height: 28),

              // Botão analisar
              SizedBox(
                width: double.infinity,
                height: 52,
                child: ElevatedButton.icon(
                  onPressed: (_foto == null || _analisando) ? null : _analisar,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF0EA5E9),
                    disabledBackgroundColor:
                        const Color(0xFF0EA5E9).withOpacity(0.3),
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10)),
                  ),
                  icon: _analisando
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(
                              color: Colors.white, strokeWidth: 2),
                        )
                      : const Icon(Icons.search, color: Colors.white, size: 20),
                  label: Text(
                    _analisando ? 'Analisando…' : 'Analisar com Nexa IA',
                    style: const TextStyle(
                        color: Colors.white,
                        fontSize: 15,
                        fontWeight: FontWeight.w600),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showPickOptions() {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF0F1F35),
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(16))),
      builder: (_) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.camera_alt_outlined,
                  color: Color(0xFF0EA5E9)),
              title: const Text('Câmera',
                  style: TextStyle(color: Colors.white)),
              onTap: () {
                Navigator.pop(context);
                _capturar(ImageSource.camera);
              },
            ),
            ListTile(
              leading: const Icon(Icons.photo_library_outlined,
                  color: Color(0xFF0EA5E9)),
              title: const Text('Galeria',
                  style: TextStyle(color: Colors.white)),
              onTap: () {
                Navigator.pop(context);
                _capturar(ImageSource.gallery);
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _btn({
    required IconData icon,
    required String label,
    required VoidCallback onTap,
  }) {
    return OutlinedButton.icon(
      onPressed: onTap,
      style: OutlinedButton.styleFrom(
        side: const BorderSide(color: Colors.white12),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        padding: const EdgeInsets.symmetric(vertical: 10),
      ),
      icon: Icon(icon, color: const Color(0xFF0EA5E9), size: 18),
      label: Text(label,
          style: const TextStyle(color: Colors.white70, fontSize: 13)),
    );
  }

  InputDecoration _inputDeco(String hint) => InputDecoration(
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
              const BorderSide(color: Color(0xFF0EA5E9), width: 1.5),
        ),
      );
}
