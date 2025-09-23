import { useState, useCallback } from 'react';

interface AddressEntity {
  id: number;
  name: string;
}

export function useAddressSelection() {
  const [countries, setCountries] = useState<AddressEntity[]>([]);
  const [states, setStates] = useState<AddressEntity[]>([]);
  const [districts, setDistricts] = useState<AddressEntity[]>([]);
  const [subDistricts, setSubDistricts] = useState<AddressEntity[]>([]);
  const [villages, setVillages] = useState<AddressEntity[]>([]);

  const fetchCountries = useCallback(async (): Promise<void> => {
    try {
      const response = await fetch('https://pfs-be-01-buf0fwgnfgbechdu.centralus-01.azurewebsites.net/api/geographies/countries/');
      const data: AddressEntity[] = await response.json();
      setCountries(data);
        console.log('Countries:', data);
    } catch (error) {
      console.error('Error fetching countries:', error);
    }
  }, []);

  const fetchStates = useCallback(async (countryId: number): Promise<AddressEntity[]> => {
    try {
      const response = await fetch(`https://pfs-be-01-buf0fwgnfgbechdu.centralus-01.azurewebsites.net/api/geographies/states/${countryId}/`);
      const data: AddressEntity[] = await response.json();
      setStates(data);
      return data;
    } catch (error) {
      console.error('Error fetching states:', error);
      return [];
    }
  }, []);

  const fetchDistricts = useCallback(async (stateId: number): Promise<AddressEntity[]> => {
    try {
      const response = await fetch(`https://pfs-be-01-buf0fwgnfgbechdu.centralus-01.azurewebsites.net/api/geographies/districts/${stateId}/`);
      const data: AddressEntity[] = await response.json();
      setDistricts(data);
      return data;
    } catch (error) {
      console.error('Error fetching districts:', error);
      return [];
    }
  }, []);

  const fetchSubdistricts = useCallback(async (districtId: number): Promise<AddressEntity[]> => {
    try {
      const response = await fetch(`https://pfs-be-01-buf0fwgnfgbechdu.centralus-01.azurewebsites.net/api/geographies/subdistricts/${districtId}/`);
      const data: AddressEntity[] = await response.json();
      setSubDistricts(data);
      return data;
    } catch (error) {
      console.error('Error fetching subdistricts:', error);
      return [];
    }
  }, []);

  const fetchVillages = useCallback(async (subdistrictId: number): Promise<AddressEntity[]> => {
    try {
      const response = await fetch(`https://pfs-be-01-buf0fwgnfgbechdu.centralus-01.azurewebsites.net/api/geographies/villages/${subdistrictId}/`);
      const data: AddressEntity[] = await response.json();
      setVillages(data);
      return data;
    } catch (error) {
      console.error('Error fetching villages:', error);
      return [];
    }
  }, []);

  return {
    countries,
    states,
    districts,
    subDistricts,
    villages,
    fetchCountries,
    fetchStates,
    fetchDistricts,
    fetchSubdistricts,
    fetchVillages,
    setCountries,
    setStates,
    setDistricts,
    setSubDistricts,
    setVillages
  };
}
