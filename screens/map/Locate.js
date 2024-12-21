import React, { useState, useEffect } from 'react';
import { StyleSheet, View, TouchableOpacity, Text } from 'react-native';
import MapView, { Marker } from 'react-native-maps';

export default function Locate({ navigation }) {
  const defaultLocation = {
    latitude: 10.859313791905437,
    longitude: 106.60419726148713,
    latitudeDelta: 0.722,
    longitudeDelta: 0.421,
  };

  const [selectedLocation, setSelectedLocation] = useState(null);
  const [region, setRegion] = useState(defaultLocation);

  useEffect(() => {
    if (selectedLocation) {
      setRegion({
        latitude: selectedLocation.latitude,
        longitude: selectedLocation.longitude,
        latitudeDelta: 0.0922,
        longitudeDelta: 0.0421,
      });
    }
  }, [selectedLocation]);

  const handleMapPress = (event) => {
    const { latitude, longitude } = event.nativeEvent.coordinate;
    setSelectedLocation({ latitude, longitude });
  };

  const handleSaveLocation = () => {
    if (selectedLocation) {
      navigation.navigate('HomeScreen', { selectedLocation });
    }
  };

  return (
    <View style={styles.container}>
      <MapView 
        style={styles.map} 
        region={region} 
        onPress={handleMapPress}
      >
        {selectedLocation && <Marker coordinate={selectedLocation} />}
      </MapView>
        <View style={{position:'absolute', bottom:'2%', alignSelf: 'center' }}>
        <TouchableOpacity  onPress={handleSaveLocation}>
          <Text style={{ backgroundColor: "#7f0d00", color: "white", fontWeight: 'bold', padding: 10, borderRadius:15 }}>Lưu địa chỉ</Text>
        </TouchableOpacity>
        </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  map: {
    flex: 1,
  },
});
