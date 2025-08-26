import { useState, useEffect } from 'react';
import api from '../../../../../api';
import { AddressOption } from '../types';

export const useAddressSelection = () => {
  const [countries, setCountries] = useState<AddressOption[]>([]);
  const [states, setStates] = useState<AddressOption[]>([]);
  const [districts, setDistricts] = useState<AddressOption[]>([]);
  const [subDistricts, setSubDistricts] = useState<AddressOption[]>([]);
  const [villages, setVillages] = useState<AddressOption[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCountries = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/countries/');
      setCountries(response.data as AddressOption[]);
    } catch (err) {
      setError('Failed to fetch countries');
      console.error('Error fetching countries:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchStates = async (countryId: number) => {
    try {
      setLoading(true);
      const response = await api.get(`/api/states/?country_id=${countryId}`);
      setStates(response.data as AddressOption[]);
    } catch (err) {
      setError('Failed to fetch states');
      console.error('Error fetching states:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchDistricts = async (stateId: number) => {
    try {
      setLoading(true);
      const response = await api.get(`/api/districts/?state_id=${stateId}`);
      setDistricts(response.data as AddressOption[]);
    } catch (err) {
      setError('Failed to fetch districts');
      console.error('Error fetching districts:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchSubdistricts = async (districtId: number) => {
    try {
      setLoading(true);
      const response = await api.get(`/api/subdistricts/?district_id=${districtId}`);
      setSubDistricts(response.data as AddressOption[]);
    } catch (err) {
      setError('Failed to fetch subdistricts');
      console.error('Error fetching subdistricts:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchVillages = async (subdistrictId: number) => {
    try {
      setLoading(true);
      const response = await api.get(`/api/villages/?subdistrict_id=${subdistrictId}`);
      setVillages(response.data as AddressOption[]);
    } catch (err) {
      setError('Failed to fetch villages');
      console.error('Error fetching villages:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCountries();
  }, []);

  return {
    countries,
    states,
    districts,
    subDistricts,
    villages,
    loading,
    error,
    fetchCountries,
    fetchStates,
    fetchDistricts,
    fetchSubdistricts,
    fetchVillages,
    setStates,
    setDistricts,
    setSubDistricts,
    setVillages,
  };
};