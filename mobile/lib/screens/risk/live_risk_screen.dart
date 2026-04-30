import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:susanoo/providers/app_providers.dart';
import 'package:susanoo/providers/locale_provider.dart';
import 'package:susanoo/theme/app_theme.dart';
import 'package:susanoo/utils/constants.dart';

class LiveRiskScreen extends ConsumerWidget {
  const LiveRiskScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final riskAsync = ref.watch(liveRiskProvider);
    final s = ref.watch(stringsProvider);

    return Scaffold(
      backgroundColor: AppTheme.surface,
      appBar: AppBar(
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.bolt_rounded, color: AppTheme.warning, size: 22),
            const SizedBox(width: 6),
            Text(s.liveRisk,
                style: const TextStyle(fontWeight: FontWeight.w800)),
          ],
        ),
        backgroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: () {
              ref.invalidate(liveRiskProvider);
              ref.invalidate(liveWeatherProvider);
            },
          ),
        ],
      ),
      body: riskAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => _ErrorView(onRetry: () {
          ref.invalidate(liveRiskProvider);
          ref.invalidate(liveWeatherProvider);
        }),
        data: (data) => _RiskBody(data: data),
      ),
    );
  }
}

List<Map<String, dynamic>> _deduped(List<dynamic> disruptions) {
  final seen = <String, Map<String, dynamic>>{};
  for (final d in disruptions) {
    final m = d as Map<String, dynamic>;
    final type = m['disruption_type'] as String? ?? '';
    final dss = (m['dss_multiplier'] as num?)?.toDouble() ?? 0.0;
    final existing =
        (seen[type]?['dss_multiplier'] as num?)?.toDouble() ?? -1.0;
    if (dss > existing) seen[type] = m;
  }
  return seen.values.toList();
}

class _RiskBody extends ConsumerWidget {
  final Map<String, dynamic> data;
  const _RiskBody({required this.data});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    final worker = data['worker'] as Map<String, dynamic>? ?? {};
    final disruptions = data['active_disruptions'] as List<dynamic>? ?? [];
    final riskScore = (worker['risk_score'] as num?)?.toDouble() ?? 0.0;
    final uniqueDisruptions = _deduped(disruptions);
    final maxDss = uniqueDisruptions.isEmpty
        ? 0.0
        : uniqueDisruptions
            .map((d) => (d['dss_multiplier'] as num?)?.toDouble() ?? 0.0)
            .reduce(max);
    final overallProbability =
        uniqueDisruptions.isEmpty ? riskScore : max(riskScore, maxDss);
    final city = worker['city'] as String? ?? '';
    final platform = (worker['platform'] as String?)?.toUpperCase() ?? '';

    return RefreshIndicator(
      onRefresh: () async {
        ref.invalidate(liveRiskProvider);
        ref.invalidate(liveWeatherProvider);
      },
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Live weather card from GPS
            _LiveWeatherCard(),
            const SizedBox(height: 16),

            _RiskGauge(
                probability: overallProbability,
                city: city,
                platform: platform),
            const SizedBox(height: 20),

            _RiskFactorCard(
                riskScore: riskScore, disruptions: uniqueDisruptions),
            const SizedBox(height: 20),

            if (uniqueDisruptions.isNotEmpty) ...[
              Text(s.activeRiskFactors,
                  style: const TextStyle(
                      fontSize: 16, fontWeight: FontWeight.w700)),
              const SizedBox(height: 10),
              ...uniqueDisruptions
                  .map((d) => _DisruptionRiskTile(disruption: d)),
              const SizedBox(height: 20),
            ],

            _RiskAdviceCard(probability: overallProbability),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }
}

// ── Live Weather Card ──────────────────────────────────────────────────────────
class _LiveWeatherCard extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final weatherAsync = ref.watch(liveWeatherProvider);
    final s = ref.watch(stringsProvider);

    return weatherAsync.when(
      loading: () => Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: AppTheme.divider, width: 0.5),
        ),
        child: Row(
          children: [
            const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(strokeWidth: 2)),
            const SizedBox(width: 12),
            Text(s.fetchingLiveWeather,
                style: const TextStyle(color: AppTheme.textSecondary)),
          ],
        ),
      ),
      error: (_, __) => const SizedBox.shrink(),
      data: (w) {
        final temp = (w['temperature_c'] as num?)?.toDouble();
        final feelsLike = (w['feels_like_c'] as num?)?.toDouble();
        final humidity = (w['humidity'] as num?)?.toInt();
        final wind = (w['wind_kmh'] as num?)?.toDouble();
        final desc = w['description'] as String? ?? '';
        final cityName = w['city_name'] as String? ?? '';
        final aqi = (w['aqi'] as num?)?.toInt();
        final pm25 = (w['pm2_5'] as num?)?.toDouble();
        final rainfall = (w['rainfall_mm_per_hr'] as num?)?.toDouble() ?? 0.0;
        final visibility = (w['visibility_km'] as num?)?.toDouble();

        final aqiColor = aqi == null
            ? AppTheme.textSecondary
            : aqi > 300
                ? AppTheme.danger
                : aqi > 200
                    ? AppTheme.warning
                    : AppTheme.success;
        final aqiLabel = aqi == null
            ? '—'
            : aqi > 300
                ? s.veryPoor
                : aqi > 200
                    ? s.poor
                    : aqi > 100
                        ? s.moderate
                        : s.good;

        return Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [Color(0xFF1A56DB), Color(0xFF0EA5E9)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(20),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(Icons.location_on_rounded,
                      color: Colors.white70, size: 14),
                  const SizedBox(width: 4),
                  Text(
                    cityName.isNotEmpty ? cityName : s.city,
                    style: const TextStyle(color: Colors.white70, fontSize: 13),
                  ),
                  const Spacer(),
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Text('LIVE',
                        style: TextStyle(
                            color: Colors.white,
                            fontSize: 10,
                            fontWeight: FontWeight.w800,
                            letterSpacing: 1)),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    temp != null ? '${temp.toInt()}°C' : '--',
                    style: const TextStyle(
                        fontSize: 48,
                        fontWeight: FontWeight.w900,
                        color: Colors.white,
                        height: 1),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(desc,
                            style: const TextStyle(
                                color: Colors.white,
                                fontSize: 14,
                                fontWeight: FontWeight.w600)),
                        if (feelsLike != null)
                          Text('Feels like ${feelsLike.toInt()}°C',
                              style: const TextStyle(
                                  color: Colors.white70, fontSize: 12)),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              // Stats row
              Row(
                children: [
                  _WeatherStat(
                      icon: Icons.water_drop_rounded,
                      label: s.humidity,
                      value: humidity != null ? '$humidity%' : '--'),
                  _WeatherStat(
                      icon: Icons.air_rounded,
                      label: s.wind,
                      value: wind != null ? '${wind.toInt()} km/h' : '--'),
                  if (rainfall > 0)
                    _WeatherStat(
                        icon: Icons.umbrella_rounded,
                        label: s.rain,
                        value: '${rainfall.toStringAsFixed(1)} mm/h'),
                  if (visibility != null)
                    _WeatherStat(
                        icon: Icons.visibility_rounded,
                        label: s.visibility,
                        value: '${visibility} km'),
                ],
              ),
              const SizedBox(height: 12),
              // AQI row
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.air, color: Colors.white, size: 16),
                    const SizedBox(width: 8),
                    Text('AQI ${aqi ?? '--'}',
                        style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.w700,
                            fontSize: 14)),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: aqiColor.withOpacity(0.25),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(aqiLabel,
                          style: TextStyle(
                              color: Colors.white,
                              fontSize: 11,
                              fontWeight: FontWeight.w700)),
                    ),
                    if (pm25 != null) ...[
                      const Spacer(),
                      Text('PM2.5: ${pm25.toStringAsFixed(1)} µg/m³',
                          style: const TextStyle(
                              color: Colors.white70, fontSize: 11)),
                    ],
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _WeatherStat extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  const _WeatherStat(
      {required this.icon, required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        children: [
          Icon(icon, color: Colors.white70, size: 18),
          const SizedBox(height: 2),
          Text(value,
              style: const TextStyle(
                  color: Colors.white,
                  fontSize: 12,
                  fontWeight: FontWeight.w700)),
          Text(label,
              style: const TextStyle(color: Colors.white60, fontSize: 10)),
        ],
      ),
    );
  }
}

// ── Animated Gauge ─────────────────────────────────────────────────────────────
class _RiskGauge extends StatefulWidget {
  final double probability;
  final String city;
  final String platform;
  const _RiskGauge(
      {required this.probability, required this.city, required this.platform});

  @override
  State<_RiskGauge> createState() => _RiskGaugeState();
}

class _RiskGaugeState extends State<_RiskGauge>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<double> _anim;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 1200));
    _anim = Tween<double>(begin: 0, end: widget.probability)
        .animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeOutCubic));
    _ctrl.forward();
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  Color _colorFor(double v) {
    if (v < 0.35) return AppTheme.success;
    if (v < 0.65) return AppTheme.warning;
    return AppTheme.danger;
  }

  String _labelFor(double v, dynamic s) {
    if (v < 0.35) return s.lowRisk;
    if (v < 0.65) return s.moderateRisk;
    return s.highRisk;
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _anim,
      builder: (context, __) {
        final s = ProviderScope.containerOf(context).read(stringsProvider);
        final v = _anim.value;
        final color = _colorFor(v);
        return Container(
          width: double.infinity,
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: color.withOpacity(0.3)),
            boxShadow: [
              BoxShadow(
                  color: color.withOpacity(0.12),
                  blurRadius: 16,
                  spreadRadius: 2)
            ],
          ),
          child: Column(
            children: [
              Text(s.riskProbability,
                  style: const TextStyle(
                      fontSize: 13,
                      color: AppTheme.textSecondary,
                      fontWeight: FontWeight.w600)),
              const SizedBox(height: 16),
              SizedBox(
                width: 180,
                height: 180,
                child: CustomPaint(
                  painter: _GaugePainter(value: v, color: color),
                  child: Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text('${(v * 100).toInt()}%',
                            style: TextStyle(
                                fontSize: 40,
                                fontWeight: FontWeight.w900,
                                color: color)),
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: color.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(_labelFor(v, s),
                              style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.w800,
                                  color: color)),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 12),
              Text('${widget.city} • ${widget.platform}',
                  style: const TextStyle(
                      fontSize: 13, color: AppTheme.textSecondary)),
            ],
          ),
        );
      },
    );
  }
}

class _GaugePainter extends CustomPainter {
  final double value;
  final Color color;
  const _GaugePainter({required this.value, required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2 - 12;
    const startAngle = pi * 0.75;
    const sweepTotal = pi * 1.5;

    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      startAngle,
      sweepTotal,
      false,
      Paint()
        ..color = AppTheme.divider
        ..strokeWidth = 14
        ..style = PaintingStyle.stroke
        ..strokeCap = StrokeCap.round,
    );
    if (value > 0) {
      canvas.drawArc(
        Rect.fromCircle(center: center, radius: radius),
        startAngle,
        sweepTotal * value,
        false,
        Paint()
          ..color = color
          ..strokeWidth = 14
          ..style = PaintingStyle.stroke
          ..strokeCap = StrokeCap.round,
      );
    }
  }

  @override
  bool shouldRepaint(_GaugePainter old) =>
      old.value != value || old.color != color;
}

// ── Risk Factor Breakdown ──────────────────────────────────────────────────────
class _RiskFactorCard extends ConsumerWidget {
  final double riskScore;
  final List<Map<String, dynamic>> disruptions;
  const _RiskFactorCard({required this.riskScore, required this.disruptions});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppTheme.divider, width: 0.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(s.riskFactorBreakdown,
              style:
                  const TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
          const SizedBox(height: 16),
          _FactorRow(
            label: s.personalRiskScore,
            value: riskScore,
            icon: Icons.person_rounded,
            color: AppTheme.primary,
          ),
          ...disruptions.map((d) => _FactorRow(
                label: AppConstants.disruptionLabels[d['disruption_type']] ??
                    '${d['disruption_type']}',
                value: (d['dss_multiplier'] as num?)?.toDouble() ?? 0.0,
                icon: Icons.warning_rounded,
                color: Color(
                    AppConstants.severityColors[d['severity']] ?? 0xFFF59E0B),
              )),
        ],
      ),
    );
  }
}

class _FactorRow extends StatefulWidget {
  final String label;
  final double value;
  final IconData icon;
  final Color color;
  const _FactorRow(
      {required this.label,
      required this.value,
      required this.icon,
      required this.color});

  @override
  State<_FactorRow> createState() => _FactorRowState();
}

class _FactorRowState extends State<_FactorRow>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<double> _anim;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 900));
    _anim = Tween<double>(begin: 0, end: widget.value)
        .animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeOutCubic));
    Future.delayed(const Duration(milliseconds: 200), () {
      if (mounted) _ctrl.forward();
    });
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(widget.icon, size: 16, color: widget.color),
              const SizedBox(width: 6),
              Expanded(
                  child: Text(widget.label,
                      style: const TextStyle(
                          fontSize: 13, color: AppTheme.textSecondary))),
              AnimatedBuilder(
                animation: _anim,
                builder: (_, __) => Text(
                  '${(_anim.value * 100).toInt()}%',
                  style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                      color: widget.color),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          AnimatedBuilder(
            animation: _anim,
            builder: (_, __) => ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: _anim.value,
                minHeight: 6,
                backgroundColor: AppTheme.divider,
                valueColor: AlwaysStoppedAnimation<Color>(widget.color),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Per-disruption tile ────────────────────────────────────────────────────────
class _DisruptionRiskTile extends StatelessWidget {
  final Map<String, dynamic> disruption;
  const _DisruptionRiskTile({required this.disruption});

  @override
  Widget build(BuildContext context) {
    final type = disruption['disruption_type'] as String? ?? '';
    final severity = disruption['severity'] as String? ?? 'moderate';
    final dss = (disruption['dss_multiplier'] as num?)?.toDouble() ?? 0.0;
    final rawValue = (disruption['raw_value'] as num?)?.toDouble();
    final description = disruption['description'] as String?;
    final label = AppConstants.disruptionLabels[type] ?? type;
    final severityColor =
        Color(AppConstants.severityColors[severity] ?? 0xFFF59E0B);
    final city = disruption['city'] as String? ?? '';

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: severityColor.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: severityColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(Icons.warning_amber_rounded,
                color: severityColor, size: 22),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label,
                    style: const TextStyle(
                        fontWeight: FontWeight.w700, fontSize: 14)),
                Text('$city • ${severity.toUpperCase()}',
                    style: const TextStyle(
                        fontSize: 12, color: AppTheme.textSecondary)),
                if (description != null) ...[
                  const SizedBox(height: 2),
                  Text(description,
                      style: const TextStyle(
                          fontSize: 11, color: AppTheme.textHint),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis),
                ],
                const SizedBox(height: 6),
                ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: dss,
                    minHeight: 5,
                    backgroundColor: AppTheme.divider,
                    valueColor: AlwaysStoppedAnimation<Color>(severityColor),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text('${(dss * 100).toInt()}%',
                  style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w800,
                      color: severityColor)),
              if (rawValue != null)
                Text(rawValue.toStringAsFixed(1),
                    style: const TextStyle(
                        fontSize: 11, color: AppTheme.textHint)),
            ],
          ),
        ],
      ),
    );
  }
}

// ── Advice Card ────────────────────────────────────────────────────────────────
class _RiskAdviceCard extends ConsumerWidget {
  final double probability;
  const _RiskAdviceCard({required this.probability});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    final isHigh = probability >= 0.65;
    final isMid = probability >= 0.35;
    final color = isHigh
        ? AppTheme.danger
        : isMid
            ? AppTheme.warning
            : AppTheme.success;
    final icon = isHigh
        ? Icons.crisis_alert_rounded
        : isMid
            ? Icons.info_rounded
            : Icons.check_circle_rounded;

    final title = isHigh
        ? '${s.highRisk} — Consider Filing a Claim'
        : isMid
            ? '${s.moderateRisk} — Stay Alert'
            : '${s.lowRisk} — You\'re Good!';

    final body = isHigh
        ? 'Active disruptions are significantly impacting your delivery zone. If you have an active policy, your claim may be auto-triggered.'
        : isMid
            ? 'Some disruptions are present in your area. Monitor conditions and ensure your policy is active.'
            : 'No significant disruptions detected. Your delivery zone looks clear right now.';

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: color.withOpacity(0.07),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withOpacity(0.25)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 26),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title,
                    style: TextStyle(
                        fontWeight: FontWeight.w700,
                        fontSize: 14,
                        color: color)),
                const SizedBox(height: 6),
                Text(body,
                    style: const TextStyle(
                        fontSize: 13,
                        color: AppTheme.textSecondary,
                        height: 1.5)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  final VoidCallback onRetry;
  const _ErrorView({required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.cloud_off_rounded,
              size: 48, color: AppTheme.textHint),
          const SizedBox(height: 12),
          const Text('Could not load risk data',
              style: TextStyle(color: AppTheme.textSecondary)),
          const SizedBox(height: 16),
          ElevatedButton(onPressed: onRetry, child: const Text('Retry')),
        ],
      ),
    );
  }
}
