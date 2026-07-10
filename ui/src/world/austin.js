/**
 * Austin address book — the demo world's "geocoder".
 * Mirrors the seed world (scripts/generate_seed.py): the depot plus known
 * good delivery points around town. No paid geocoding APIs: pick from the
 * book or click the map.
 */

export const AUSTIN_CENTER = { latitude: 30.2672, longitude: -97.7431 };

export const DEPOT = {
  label: 'Eastside Depot',
  address: '2401 E 6th St, Austin, TX 78702',
  latitude: 30.2601,
  longitude: -97.7185,
};

export const ADDRESS_BOOK = [
  { address: '904 West Ave, Austin, TX 78701', latitude: 30.2734, longitude: -97.7484 },
  { address: '1804 E Cesar Chavez St, Austin, TX 78702', latitude: 30.256, longitude: -97.7228 },
  { address: '3809 Duval St, Austin, TX 78751', latitude: 30.3037, longitude: -97.7288 },
  { address: '2604 S 5th St, Austin, TX 78704', latitude: 30.2372, longitude: -97.7644 },
  { address: '1401 Rosewood Ave, Austin, TX 78702', latitude: 30.2683, longitude: -97.7229 },
  { address: '5300 Airport Blvd, Austin, TX 78751', latitude: 30.3131, longitude: -97.7126 },
  { address: '807 W Mary St, Austin, TX 78704', latitude: 30.2489, longitude: -97.7583 },
  { address: '3401 Cherrywood Rd, Austin, TX 78722', latitude: 30.2926, longitude: -97.7146 },
  { address: '1200 Barton Hills Dr, Austin, TX 78704', latitude: 30.2547, longitude: -97.7789 },
  { address: '6800 Burnet Rd, Austin, TX 78757', latitude: 30.3437, longitude: -97.7405 },
  { address: '2002 Manor Rd, Austin, TX 78722', latitude: 30.2841, longitude: -97.7186 },
  { address: '400 E Riverside Dr, Austin, TX 78704', latitude: 30.2447, longitude: -97.7401 },
  { address: '4700 Grover Ave, Austin, TX 78756', latitude: 30.3178, longitude: -97.7419 },
  { address: '1913 E 12th St, Austin, TX 78702', latitude: 30.2735, longitude: -97.7176 },
  { address: '2525 W Anderson Ln, Austin, TX 78757', latitude: 30.3593, longitude: -97.7317 },
  { address: '1100 S Lamar Blvd, Austin, TX 78704', latitude: 30.2559, longitude: -97.7635 },
  { address: '5400 Manchaca Rd, Austin, TX 78745', latitude: 30.2172, longitude: -97.7965 },
  { address: '3300 Bee Caves Rd, Austin, TX 78746', latitude: 30.2731, longitude: -97.8018 },
  { address: '7301 Woodrow Ave, Austin, TX 78757', latitude: 30.3474, longitude: -97.7326 },
  { address: '2200 E 7th St, Austin, TX 78702', latitude: 30.2593, longitude: -97.7157 },
  { address: '600 Congress Ave, Austin, TX 78701', latitude: 30.268, longitude: -97.7431 },
  { address: '4200 Red River St, Austin, TX 78751', latitude: 30.3013, longitude: -97.7245 },
  { address: '1717 Toomey Rd, Austin, TX 78704', latitude: 30.2617, longitude: -97.7615 },
  { address: '5555 N Lamar Blvd, Austin, TX 78751', latitude: 30.3221, longitude: -97.7267 },
  { address: '1304 E 51st St, Austin, TX 78723', latitude: 30.3054, longitude: -97.7099 },
  { address: '901 W Ben White Blvd, Austin, TX 78704', latitude: 30.2278, longitude: -97.7756 },
  { address: '3663 Bee Caves Rd, Austin, TX 78746', latitude: 30.2705, longitude: -97.809 },
  { address: '1601 E 38th 1/2 St, Austin, TX 78722', latitude: 30.2969, longitude: -97.7194 },
  { address: '500 E Anderson Ln, Austin, TX 78752', latitude: 30.3541, longitude: -97.7043 },
  { address: '2901 Montopolis Dr, Austin, TX 78741', latitude: 30.2287, longitude: -97.704 },
];
