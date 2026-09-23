class Usuario {
  final int id;
  final String nome;
  final String cargo;
  final String token;

  const Usuario({
    required this.id,
    required this.nome,
    required this.cargo,
    required this.token,
  });

  factory Usuario.fromJson(Map<String, dynamic> j, String token) => Usuario(
        id: j['id'] as int,
        nome: j['nome'] as String? ?? '',
        cargo: j['cargo'] as String? ?? '',
        token: token,
      );
}

class Anomalia {
  final String rotulo;
  final String severidade;
  final double confianca;
  final String componente;
  final String descricao;
  final String causaProvavel;
  final String recomendacao;
  final String icone;
  // overlay em % para a imagem
  final double left;
  final double top;
  final double width;
  final double height;

  const Anomalia({
    required this.rotulo,
    required this.severidade,
    required this.confianca,
    required this.componente,
    required this.descricao,
    required this.causaProvavel,
    required this.recomendacao,
    required this.icone,
    required this.left,
    required this.top,
    required this.width,
    required this.height,
  });

  factory Anomalia.fromJson(Map<String, dynamic> j) => Anomalia(
        rotulo: j['rotulo'] as String? ?? '',
        severidade: j['severidade'] as String? ?? 'info',
        confianca: (j['confianca'] as num?)?.toDouble() ?? 0.5,
        componente: j['componente'] as String? ?? '',
        descricao: j['descricao'] as String? ?? '',
        causaProvavel: j['causa_provavel'] as String? ?? '',
        recomendacao: j['recomendacao'] as String? ?? '',
        icone: j['icone'] as String? ?? '',
        left: (j['left'] as num?)?.toDouble() ?? 0,
        top: (j['top'] as num?)?.toDouble() ?? 0,
        width: (j['width'] as num?)?.toDouble() ?? 10,
        height: (j['height'] as num?)?.toDouble() ?? 10,
      );
}

class ResultadoSensor {
  final List<Anomalia> anomalias;
  final int? score;
  final String severidadeMax;
  final String resumo;
  final String modelo;
  final String imagemUrl;

  const ResultadoSensor({
    required this.anomalias,
    required this.score,
    required this.severidadeMax,
    required this.resumo,
    required this.modelo,
    required this.imagemUrl,
  });

  factory ResultadoSensor.fromJson(Map<String, dynamic> j) => ResultadoSensor(
        anomalias: (j['anomalias'] as List? ?? [])
            .map((e) => Anomalia.fromJson(e as Map<String, dynamic>))
            .toList(),
        score: j['score'] as int?,
        severidadeMax: j['severidade_max'] as String? ?? 'ok',
        resumo: j['resumo'] as String? ?? '',
        modelo: j['modelo'] as String? ?? '',
        imagemUrl: j['imagem_url'] as String? ?? '',
      );
}

class ProblemaDocumento {
  final String tipo;
  final String campo;
  final String descricao;
  final String sugestao;
  final String severidade;

  const ProblemaDocumento({
    required this.tipo,
    required this.campo,
    required this.descricao,
    required this.sugestao,
    required this.severidade,
  });

  factory ProblemaDocumento.fromJson(Map<String, dynamic> j) =>
      ProblemaDocumento(
        tipo: j['tipo'] as String? ?? '',
        campo: j['campo'] as String? ?? '',
        descricao: j['descricao'] as String? ?? '',
        sugestao: j['sugestao'] as String? ?? '',
        severidade: j['severidade'] as String? ?? 'medio',
      );
}

class ResultadoDocumento {
  final List<ProblemaDocumento> problemas;
  final int score;
  final String resumo;
  final String modelo;

  const ResultadoDocumento({
    required this.problemas,
    required this.score,
    required this.resumo,
    required this.modelo,
  });

  factory ResultadoDocumento.fromJson(Map<String, dynamic> j) =>
      ResultadoDocumento(
        problemas: (j['problemas'] as List? ?? [])
            .map((e) => ProblemaDocumento.fromJson(e as Map<String, dynamic>))
            .toList(),
        score: j['score'] as int? ?? 100,
        resumo: j['resumo'] as String? ?? '',
        modelo: j['modelo'] as String? ?? '',
      );
}

class Maquina {
  final int id;
  final String nome;
  final String setor;

  const Maquina({required this.id, required this.nome, required this.setor});

  factory Maquina.fromJson(Map<String, dynamic> j) => Maquina(
        id: j['id'] as int,
        nome: j['nome'] as String? ?? '',
        setor: j['setor'] as String? ?? '',
      );

  @override
  String toString() => nome;
}

class Ocorrencia {
  final int id;
  final String maquinaNome;
  final String descricao;
  final String tipoOcorrencia;
  final String nivelImpacto;
  final String status;
  final String dataOcorrencia;

  const Ocorrencia({
    required this.id,
    required this.maquinaNome,
    required this.descricao,
    required this.tipoOcorrencia,
    required this.nivelImpacto,
    required this.status,
    required this.dataOcorrencia,
  });

  factory Ocorrencia.fromJson(Map<String, dynamic> j) => Ocorrencia(
        id: j['id'] as int,
        maquinaNome: j['maquina_nome'] as String? ?? '',
        descricao: j['descricao'] as String? ?? '',
        tipoOcorrencia: j['tipo_ocorrencia'] as String? ?? '',
        nivelImpacto: j['nivel_impacto'] as String? ?? '',
        status: j['status'] as String? ?? '',
        dataOcorrencia: j['data_ocorrencia'] as String? ?? '',
      );
}
