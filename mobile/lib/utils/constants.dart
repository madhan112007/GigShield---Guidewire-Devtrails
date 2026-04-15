class AppConstants {
  static const String baseUrl = String.fromEnvironment(
    'BASE_URL',
    defaultValue: 'http://16.112.121.102:8000/api/v1',
  );

  static const String accessTokenKey = 'access_token';
  static const String refreshTokenKey = 'refresh_token';
  static const String workerIdKey = 'worker_id';
  static const String onboardingDoneKey = 'onboarding_done';
  static const String termsAcceptedKey = 'terms_accepted';

  static const Map<String, String> tierLabels = {
    'basic': 'Basic Shield',
    'smart': 'Smart Shield',
    'pro': 'Pro Shield',
  };

  static const Map<String, double> tierBasePrices = {
    'basic': 29.0,
    'smart': 49.0,
    'pro': 79.0,
  };

  // Disruption icons — use Icons.* in UI, labels are plain text
  static const Map<String, String> disruptionLabels = {
    'heavy_rain': 'Heavy Rain',
    'extreme_heat': 'Extreme Heat',
    'aqi_spike': 'AQI Spike',
    'traffic_disruption': 'Traffic Disruption',
    'civic_emergency': 'Civic Emergency',
  };

  // Map disruption type to Material icon
  static const Map<String, int> disruptionIcons = {
    'heavy_rain': 0xe798,        // Icons.water_drop_rounded
    'extreme_heat': 0xf076b,     // Icons.thermostat_rounded
    'aqi_spike': 0xe044,         // Icons.air_rounded
    'traffic_disruption': 0xe531, // Icons.traffic_rounded
    'civic_emergency': 0xe7f4,   // Icons.emergency_rounded
  };

  static const Map<String, int> severityColors = {
    'moderate': 0xFFF59E0B,
    'severe': 0xFFEF4444,
    'extreme': 0xFF991B1B,
  };

  static const List<String> supportedCities = [
    'Bangalore', 'Mumbai', 'Delhi', 'Chennai',
    'Hyderabad', 'Pune', 'Kolkata',
  ];

  static const List<Map<String, String>> platforms = [
    {'value': 'blinkit',          'label': 'Blinkit',          'color': 'F8C002'},
    {'value': 'zepto',            'label': 'Zepto',            'color': '6C2BF5'},
    {'value': 'swiggy_instamart', 'label': 'Swiggy Instamart', 'color': 'FC8019'},
    {'value': 'zomato',           'label': 'Zomato',           'color': 'E23744'},
    {'value': 'amazon',           'label': 'Amazon',           'color': 'FF9900'},
    {'value': 'bigbasket',        'label': 'BigBasket',        'color': '84C225'},
  ];
}
