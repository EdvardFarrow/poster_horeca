import EmployeeDashboard from './EmployeeDashboard/EmployeeDashboard';
import ManagerDashboard from './ManagerDashboard/ManagerDashboard';
import OwnerDashboard from '../OwnerDashboard/OwnerDashboard';

const Home = ({ user }) => {
    switch(user.role) {
        case 'manager':
            return <ManagerDashboard />;
        case 'owner':
            return <OwnerDashboard />; 
        default:
            return <EmployeeDashboard />;
    }
};
