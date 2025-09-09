// AdminPendingUsers.tsx
import React, { useState, useEffect } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  TablePagination,
  Chip,
  Box,
  Typography,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  ButtonGroup,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Avatar,
} from '@mui/material';
import api from '../../../api';
import './AdminPendingUsers.css'; // Import the CSS file

interface NoInitiatorData {
  id: number;
  phone_number: string | null;
  verification_status: string;
  claimed_by: number | null;
  claimed_by_name: string | null;
  claimed_at: string | null;
  verified_by: number | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

interface PendingUser {
  id: number;
  gmail: string;
  first_name: string;
  last_name: string;
  profile_picture: string | null;
  date_of_birth: string;
  gender: string;
  country_name: string | null;
  state_name: string | null;
  district_name: string | null;
  subdistrict_name: string | null;
  village_name: string | null;
  is_verified: boolean;
  event_type: string;
  event_id: number | null;
  no_initiator_data: NoInitiatorData | null;
}

interface PendingUsersResponse {
  results: PendingUser[];
  count: number;
}

const AdminPendingUsers: React.FC = () => {
  const [users, setUsers] = useState<PendingUser[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState<number>(0);
  const [rowsPerPage, setRowsPerPage] = useState<number>(20);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [verificationStatus, setVerificationStatus] = useState<string>('');
  const [noteDialogOpen, setNoteDialogOpen] = useState<boolean>(false);
  const [currentUser, setCurrentUser] = useState<PendingUser | null>(null);
  const [notes, setNotes] = useState<string>('');
  const [currentAdminId, setCurrentAdminId] = useState<number | null>(null);

  // --- New Interfaces for Verify Response ---
interface Petitioner {
  id: number;
  gmail: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  country: string | null;
  state: string | null;
  district: string | null;
  subdistrict: string | null;
  village: string | null;
}

interface UserTree {
  id: number;
  name: string;
  profilepic: string | null;
  parentid: number | null;
  event_choice: string | null;
  event_id: number | null;
}

interface VerifyResponse {
  message: string;
  petitioner: Petitioner;
  user_tree: UserTree;
}

  useEffect(() => {
    // Get admin ID from localStorage
    const userId = localStorage.getItem('user_id');
    if (userId) {
      setCurrentAdminId(parseInt(userId));
    }
  }, []);

  const fetchPendingUsers = async () => {
    try {
      setLoading(true);
      const params: any = { page: page + 1, page_size: rowsPerPage };
      if (verificationStatus) {
        params.verification_status = verificationStatus;
      }
      const response = await api.get<PendingUsersResponse>(
        'api/pendingusers/admin/pending-users/no-initiator/',
        { params }
      );
      setUsers(response.data.results);
      setTotalCount(response.data.count);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to fetch pending users');
      if (err.response?.status === 403) {
        // Handle unauthorized access if needed
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (currentAdminId !== null) {
      fetchPendingUsers();
    }
  }, [page, rowsPerPage, verificationStatus, currentAdminId]);

  const handleClaimUser = async (userId: number) => {
    try {
      await api.post(`api/pendingusers/admin/pending-users/${userId}/claim/`);
      fetchPendingUsers();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to claim user');
    }
  };

  const handleVerifyUser = async (userId: number) => {
    try {
      const response = await api.post<VerifyResponse>(
        `api/pendingusers/admin/pending-users/${userId}/verify/`
      );

      const transferredUser = response.data;
      setError(null);

      alert(`User verified and transferred successfully!
        Petitioner ID: ${transferredUser.petitioner.id}
        Name: ${transferredUser.petitioner.first_name} ${transferredUser.petitioner.last_name}
        Email: ${transferredUser.petitioner.gmail}
        User Tree ID: ${transferredUser.user_tree.id}
      `);

      fetchPendingUsers();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to verify user');
    }
  };

  const handleUnclaimUser = async (userId: number) => {
    try {
      await api.post(`api/pendingusers/admin/pending-users/${userId}/unclaim/`);
      fetchPendingUsers();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to unclaim user');
    }
  };

  const handleAddNotes = (user: PendingUser) => {
    setCurrentUser(user);
    setNotes(user.no_initiator_data?.notes || '');
    setNoteDialogOpen(true);
  };

  const handleSaveNotes = async () => {
    if (!currentUser) return;
    try {
      await api.patch(
        `api/pendingusers/admin/pending-users/${currentUser.id}/notes/`,
        { notes }
      );
      setNoteDialogOpen(false);
      fetchPendingUsers();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to save notes');
    }
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'verified':
        return 'success';
      case 'claimed':
        return 'warning';
      case 'unclaimed':
        return 'default';
      case 'spam':
        return 'error';
      default:
        return 'default';
    }
  };

  const canClaimOrVerify = (user: PendingUser) => {
    if (!user.no_initiator_data || !currentAdminId) return false;

    const isClaimed = user.no_initiator_data.verification_status === 'claimed';
    const isClaimedByMe = user.no_initiator_data.claimed_by === currentAdminId;

    return !isClaimed || isClaimedByMe;
  };

  if (loading && users.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box className="apu-container">
      <Typography variant="h4" gutterBottom className="apu-title">
        Pending Users Without Initiators
      </Typography>
      <FormControl sx={{ minWidth: 200, mb: 2 }} className="apu-filter-control">
        <InputLabel>Verification Status</InputLabel>
        <Select
          value={verificationStatus}
          label="Verification Status"
          onChange={(e) => setVerificationStatus(e.target.value)}
        >
          <MenuItem value="">All</MenuItem>
          <MenuItem value="unclaimed">Unclaimed</MenuItem>
          <MenuItem value="claimed">Claimed</MenuItem>
          <MenuItem value="verified">Verified</MenuItem>
          <MenuItem value="spam">Spam</MenuItem>
        </Select>
      </FormControl>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} className="apu-alert">
          {error}
        </Alert>
      )}
      <TableContainer component={Paper} className="apu-table-container">
        <Table className="apu-table">
          <TableHead className="apu-table-head">
            <TableRow>
              <TableCell className="apu-table-head-cell">ID</TableCell>
              <TableCell className="apu-table-head-cell">Profile</TableCell>
              <TableCell className="apu-table-head-cell">Email</TableCell>
              <TableCell className="apu-table-head-cell">Name</TableCell>
              <TableCell className="apu-table-head-cell">Date of Birth</TableCell>
              <TableCell className="apu-table-head-cell">Gender</TableCell>
              <TableCell className="apu-table-head-cell">Location</TableCell>
              <TableCell className="apu-table-head-cell">Status</TableCell>
              <TableCell className="apu-table-head-cell">Claimed By</TableCell>
              <TableCell className="apu-table-head-cell">Phone Number</TableCell>
              <TableCell className="apu-table-head-cell">Notes</TableCell>
              <TableCell className="apu-table-head-cell">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {users.map((user) => (
              <TableRow key={user.id}>
                <TableCell className="apu-table-cell">{user.id}</TableCell>
                <TableCell className="apu-table-cell">
                  {user.profile_picture ? (
                    <Avatar
                      src={user.profile_picture}
                      alt={`${user.first_name} ${user.last_name}`}
                      className="apu-avatar"
                    />
                  ) : (
                    <Avatar className="apu-avatar">
                      {user.first_name?.[0]}
                      {user.last_name?.[0]}
                    </Avatar>
                  )}
                </TableCell>
                <TableCell className="apu-table-cell">{user.gmail}</TableCell>
                <TableCell className="apu-table-cell">
                  {user.first_name} {user.last_name}
                </TableCell>
                <TableCell className="apu-table-cell">{user.date_of_birth}</TableCell>
                <TableCell className="apu-table-cell">{user.gender}</TableCell>
                <TableCell className="apu-table-cell">
                  {[user.village_name, user.subdistrict_name, user.district_name, user.state_name, user.country_name]
                    .filter(Boolean)
                    .join(', ')}
                </TableCell>
                <TableCell className="apu-table-cell">
                  {user.no_initiator_data ? (
                    <Chip
                      label={user.no_initiator_data.verification_status}
                      color={getStatusColor(user.no_initiator_data.verification_status) as any}
                      className="apu-chip"
                    />
                  ) : (
                    <Chip label="N/A" color="default" className="apu-chip" />
                  )}
                </TableCell>
                <TableCell className="apu-table-cell">
                  {user.no_initiator_data?.claimed_by_name || 'Not claimed'}
                  {user.no_initiator_data?.claimed_at && (
                    <Typography variant="caption" display="block">
                      {new Date(user.no_initiator_data.claimed_at).toLocaleString()}
                    </Typography>
                  )}
                </TableCell>
                <TableCell className="apu-table-cell">
                  {user.no_initiator_data?.phone_number || 'N/A'}
                </TableCell>
                <TableCell className="apu-table-cell apu-notes-cell">
                  <Box>
                    <Typography variant="body2" className="apu-notes-text">
                      {user.no_initiator_data?.notes || 'No notes'}
                    </Typography>
                    <Button
                      size="small"
                      onClick={() => handleAddNotes(user)}
                      disabled={!user.no_initiator_data || !canClaimOrVerify(user)}
                    >
                      {user.no_initiator_data?.notes ? 'Edit' : 'Add'} Notes
                    </Button>
                  </Box>
                </TableCell>
                <TableCell className="apu-table-cell apu-actions-cell">
                  {user.no_initiator_data ? (
                    <ButtonGroup orientation="vertical" className="apu-button-group">
                      {user.no_initiator_data.verification_status === 'unclaimed' && (
                        <Button onClick={() => handleClaimUser(user.id)}>Claim</Button>
                      )}
                      {user.no_initiator_data.verification_status === 'claimed' && (
                        <>
                          {user.no_initiator_data.claimed_by === currentAdminId ? (
                            <>
                              <Button onClick={() => handleVerifyUser(user.id)}>Verify</Button>
                              <Button onClick={() => handleUnclaimUser(user.id)}>Unclaim</Button>
                            </>
                          ) : (
                            <Button disabled>
                              Claimed by {user.no_initiator_data.claimed_by_name}
                            </Button>
                          )}
                        </>
                      )}
                      {['verified', 'spam'].includes(user.no_initiator_data.verification_status) && (
                        <Button disabled>No action available</Button>
                      )}
                    </ButtonGroup>
                  ) : (
                    <Button disabled>No data</Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <TablePagination
        rowsPerPageOptions={[10, 20, 50]}
        component="div"
        count={totalCount}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
        className="apu-pagination"
      />
      <Dialog
        open={noteDialogOpen}
        onClose={() => setNoteDialogOpen(false)}
        maxWidth="md"
        fullWidth
        className="apu-dialog"
      >
        <DialogTitle className="apu-dialog-title">Add Notes</DialogTitle>
        <DialogContent className="apu-dialog-content">
          <TextField
            autoFocus
            margin="dense"
            label="Notes"
            fullWidth
            variant="outlined"
            multiline
            rows={4}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </DialogContent>
        <DialogActions className="apu-dialog-actions">
          <Button onClick={() => setNoteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveNotes}>Save</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AdminPendingUsers;
